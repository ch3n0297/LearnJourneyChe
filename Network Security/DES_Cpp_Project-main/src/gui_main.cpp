// src/gui_main.cpp – unified GUI for DES + 4 extra crypto tools
// --------------------------------------------------------------
// NOTE: 這份檔案取代原先 gui_main.cpp；你可以直接覆蓋。
// 若覺得功能多寡需微調，可再刪減對應 Tab 區塊或 helper 函式。

#include "imgui.h"
#include "backends/imgui_impl_glfw.h"
#include "backends/imgui_impl_opengl3.h"

#include "des.h"                   // DES 核心（已存在）
#include <GLFW/glfw3.h>

#include <cstdio>
#include <cstring>
#include <cctype>
#include <string>
#include <array>
#include <vector>
#include <iostream>

#include "tinyfiledialogs.h"        // Native file‑picker dialogs
#include <algorithm>   // shuffle
#include <numeric>     // iota
#include <random>      // mt19937, random_device

// -----------------------------------------------------------------------------
// 🛠️  Minimal helper implementations for the 4 CLI tools in "library" style
//      如果你已經把它們獨立成 .cpp/.h，可把這段刪掉並 include 對應 header。
// -----------------------------------------------------------------------------

// 1️⃣ Letter Frequency (A‥Z)
static void letterFreqFromFile(const char* path, std::array<size_t,26>& cnt, size_t& total)
{
    cnt.fill(0); total = 0;
    FILE* f = fopen(path, "r");
    if(!f) return;
    int ch;
    while((ch=fgetc(f))!=EOF){
        if(std::isalpha(static_cast<unsigned char>(ch))){
            cnt[std::toupper(ch)-'A']++; ++total;
        }
    }
    fclose(f);
}

// 2️⃣ Simple n‑bit Block Substitution – random permutation each run
static std::string runBlockSubCipher(const std::string& inBits,int n,bool encrypt)
{
    const size_t M = 1u<<n;
    static std::vector<uint8_t> key;         // 保留在靜態記憶體，GUI 執行期間共用
    if(key.size()!=M){                       // 重新產生 permutation
        key.resize(M);
        std::iota(key.begin(),key.end(),0);
        std::mt19937 rng{std::random_device{}()};
        std::shuffle(key.begin(),key.end(),rng);
    }
    std::vector<uint8_t> inv(M);
    for(size_t i=0;i<M;++i) inv[key[i]]=i;

    std::string out;
    uint32_t val=0,bits=0;
    for(char c:inBits){
        if(c!='0'&&c!='1') continue;         // ignore non-bits
        val=(val<<1)|(c=='1'); ++bits;
        if(bits==n){
            uint8_t mapped = encrypt? key[val] : inv[val];
            for(int i=n-1;i>=0;--i)
                out.push_back( ((mapped>>i)&1)?'1':'0' );
            val=0; bits=0;
        }
    }
    return out;
}

// 3️⃣ RSA fast modular exponentiation (64‑bit demo)
static unsigned long long mod_pow(unsigned long long base,unsigned long long exp,unsigned long long mod){
    unsigned long long res=1%mod;
    base%=mod;
    while(exp){
        if(exp&1) res=(__uint128_t)res*base%mod;
        base=(__uint128_t)base*base%mod;
        exp>>=1;
    }
    return res;
}

// 4️⃣ Hill 2×2 cipher (mod 29, A‑Z,. ,?)
static int sym2num(char c){
    if(c>='A'&&c<='Z') return c-'A';
    if(c==',') return 26; if(c=='.') return 27; if(c=='?') return 28; return -1;
}
static char num2sym(int n){ return n<26 ? 'A'+n : ",.?"[n-26]; }
static int mod29inv(int a){ for(int x=1;x<29;++x) if((a*x)%29==1) return x; return -1; }
static std::string runHillCipher(const std::string& txt,int K[4],bool enc){
    int det = (K[0]*K[3]-K[1]*K[2])%29; if(det<0) det+=29;
    int invDet = mod29inv(det); if(invDet==-1) return "(invalid key)";
    int Kin[4] = { K[3]*invDet%29, (29-K[1])*invDet%29,
                   (29-K[2])*invDet%29, K[0]*invDet%29 };
    const int* M = enc? K : Kin;

    std::vector<int> src;
    for(char c:txt){ int v=sym2num(std::toupper(c)); if(v!=-1) src.push_back(v); }
    if(src.size()%2) src.push_back(26);      // padding with comma
    std::string out; out.reserve(src.size());
    for(size_t i=0;i<src.size();i+=2){
        int y0 = (M[0]*src[i] + M[1]*src[i+1])%29;
        int y1 = (M[2]*src[i] + M[3]*src[i+1])%29;
        out.push_back(num2sym(y0)); out.push_back(num2sym(y1));
    }
    return out;
}

// -----------------------------------------------------------------------------
// 👇 你的原先 GUI 主程式（改為多分頁）
// -----------------------------------------------------------------------------

// Helper：將整數 key/iv 填入 bool[64]
static void initKeyIV(unsigned int keyInt, bool key64[64], bool iv64[64]) {
    memset(key64, false, 64);
    memset(iv64,  false, 64);
    for(int i=0;i<32;i++) key64[i] = ((keyInt>>i)&1)!=0;
}

int main() {
    // 1) 初始化 GLFW + OpenGL context
    if(!glfwInit()) return -1;
#ifdef __APPLE__
    const char* glsl_version = "#version 150";
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 2);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE);
#else
    const char* glsl_version = "#version 330";
#endif
    glfwWindowHint(GLFW_RESIZABLE, GLFW_TRUE);
    GLFWwindow* window = glfwCreateWindow(800, 500, "Crypto Toolbox", nullptr, nullptr);
    if(!window){ glfwTerminate(); return -1; }
    glfwMakeContextCurrent(window);
    glfwSwapInterval(1);

    // 2) ImGui init
    IMGUI_CHECKVERSION(); ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO(); (void)io;
    ImGui::StyleColorsDark();
    ImGui_ImplGlfw_InitForOpenGL(window,true);
    ImGui_ImplOpenGL3_Init(glsl_version);

    // ---------------- shared GUI states ----------------
    // DES
    int desMode=0, desOp=0; char inPath[256]="",outPath[256]=""; unsigned int keyInt=3000; bool key64[64],iv64[64];
    // Letter freq
    char freqPath[256]=""; std::array<size_t,26> freqCnt{}; size_t freqTotal=0; float freqPlot[26]{};
    // Block sub
    int nBits=4; bool subEncrypt=true; char subIn[512]="", subOut[512]="";
    // RSA
    unsigned long long rsaB=123,rsaE=65537,rsaM=1000000007,rsaRes=0;
    // Hill
    int K[4]={3,3,2,5}; char hillIn[256]="HELLO",hillOut[256]=""; bool hillEncrypt=true;

    std::string statusMsg=""; bool statusErr=false;

    // 4) 主迴圈
    while(!glfwWindowShouldClose(window)){
        glfwPollEvents();
        ImGui_ImplOpenGL3_NewFrame(); ImGui_ImplGlfw_NewFrame(); ImGui::NewFrame();

        // Main window
        ImGui::SetNextWindowSize(ImGui::GetIO().DisplaySize, ImGuiCond_FirstUseEver);
        ImGui::Begin("Crypto Toolbox");

        if(ImGui::BeginTabBar("MainTabs")){
            /* ---------------- DES Tab ---------------- */
            if(ImGui::BeginTabItem("DES")){
                ImGui::InputInt("Key (integer)",(int*)&keyInt);
                ImGui::InputText("Input", inPath,256,ImGuiInputTextFlags_ReadOnly);
                ImGui::SameLine(); if(ImGui::Button("Browse##in")){
                    const char* fp=tinyfd_openFileDialog("Open", "",0,nullptr,nullptr,0);
                    if(fp) { std::strncpy(inPath,fp,255); inPath[255]='\0'; }
                }
                ImGui::InputText("Output", outPath,256,ImGuiInputTextFlags_ReadOnly);
                ImGui::SameLine(); if(ImGui::Button("Browse##out")){
                    const char* fp=tinyfd_saveFileDialog("Save", "",0,nullptr,nullptr);
                    if(fp) { std::strncpy(outPath,fp,255); outPath[255]='\0'; }
                }
                const char* modes[]={"--","ECB","CFB","CTR"}; ImGui::Combo("Mode",&desMode,modes,IM_ARRAYSIZE(modes));
                const char* ops[]={"--","Encrypt","Decrypt"}; ImGui::Combo("Action",&desOp,ops,IM_ARRAYSIZE(ops));
                if(ImGui::Button("Execute")){
                    statusMsg.clear(); statusErr=false;
                    if(!*inPath) { statusMsg="Choose input file"; statusErr=true; }
                    else if(!*outPath){ statusMsg="Choose output file"; statusErr=true; }
                    else if(desMode==0||desOp==0){ statusMsg="Select mode/action"; statusErr=true; }
                    else {
                        initKeyIV(keyInt,key64,iv64);
                        FILE* fin=fopen(inPath,"rb"),*fout=fopen(outPath,"wb");
                        if(!fin||!fout){ statusMsg="Open file failed"; statusErr=true; }
                        else{
                            switch(desMode){
                                case 1: desOp==1? desECBEncrypt(fin,fout,key64):desECBDecrypt(fin,fout,key64); break;
                                case 2: desOp==1? desCFBEncrypt(fin,fout,iv64,key64):desCFBDecrypt(fin,fout,iv64,key64); break;
                                case 3: desCTREncryptDecrypt(fin,fout,iv64,key64); break;
                            }
                            fclose(fin);fclose(fout);
                            statusMsg="DES Done";
                        }
                    }
                }
                ImGui::EndTabItem();
            }

            /* ---------------- Letter Frequency Tab ---------------- */
            if(ImGui::BeginTabItem("Letter Freq")){
                ImGui::InputText("Text File", freqPath,256,ImGuiInputTextFlags_ReadOnly);
                ImGui::SameLine(); if(ImGui::Button("Browse##freq")){
                    const char* fp=tinyfd_openFileDialog("Open text","",0,nullptr,nullptr,0);
                    if(fp){ std::strncpy(freqPath,fp,255); }
                }
                if(ImGui::Button("Analyze")){
                    if(!*freqPath){ statusMsg="Choose text file"; statusErr=true; }
                    else {
                        letterFreqFromFile(freqPath,freqCnt,freqTotal);
                        for(int i=0;i<26;++i) freqPlot[i]=freqTotal? 100.0f*freqCnt[i]/freqTotal:0.0f;
                        statusMsg="Freq computed"; statusErr=false;
                    }
                }
                if(freqTotal){ ImGui::PlotHistogram("A-Z %", freqPlot,26,0,nullptr,0.0f,15.0f,ImVec2(0,120)); }
                ImGui::EndTabItem();
            }

            /* ---------------- Block Substitution Tab ---------------- */
            if(ImGui::BeginTabItem("Block Sub")){
                ImGui::SliderInt("n bits", &nBits,1,8);
                ImGui::Checkbox("Encrypt", &subEncrypt);
                ImGui::InputTextMultiline("Input bits", subIn,512, ImVec2(-FLT_MIN,70));
                if(ImGui::Button("Run SubCipher")){
                    std::string out = runBlockSubCipher(subIn,nBits,subEncrypt);
                    std::strncpy(subOut,out.c_str(),511);
                }
                ImGui::InputTextMultiline("Output bits", subOut,512,
                                          ImVec2(-FLT_MIN,70),ImGuiInputTextFlags_ReadOnly);
                ImGui::EndTabItem();
            }

            /* ---------------- RSA Pow Tab ---------------- */
            if(ImGui::BeginTabItem("RSA Pow")){
                ImGui::InputScalar("Base (b)", ImGuiDataType_U64, &rsaB);
                ImGui::InputScalar("Exp  (e)", ImGuiDataType_U64, &rsaE);
                ImGui::InputScalar("Mod  (m)", ImGuiDataType_U64, &rsaM);
                if(ImGui::Button("Compute b^e mod m")) rsaRes = mod_pow(rsaB,rsaE,rsaM);
                ImGui::Text("Result = %llu", rsaRes);
                ImGui::EndTabItem();
            }

            /* ---------------- Hill Cipher Tab ---------------- */
            if(ImGui::BeginTabItem("Hill 2x2")){
                ImGui::InputInt4("Key [a b; c d]", K);
                ImGui::Checkbox("Encrypt", &hillEncrypt);
                ImGui::InputText("Input", hillIn,256);
                if(ImGui::Button("Run Hill")){
                    std::string out = runHillCipher(hillIn,K,hillEncrypt);
                    std::strncpy(hillOut,out.c_str(),255);
                }
                ImGui::InputText("Output", hillOut,256,ImGuiInputTextFlags_ReadOnly);
                ImGui::EndTabItem();
            }

            ImGui::EndTabBar();
        }

        if(!statusMsg.empty()){
            ImVec4 col=statusErr?ImVec4(1,0.25f,0.25f,1):ImVec4(0.25f,1,0.25f,1);
            ImGui::Separator(); ImGui::TextColored(col,"%s",statusMsg.c_str());
        }
        ImGui::End();

        // Render loop bottom
        ImGui::Render(); int w,h; glfwGetFramebufferSize(window,&w,&h);
        glViewport(0,0,w,h); glClear(GL_COLOR_BUFFER_BIT);
        ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());
        glfwSwapBuffers(window);
    }

    // cleanup
    ImGui_ImplOpenGL3_Shutdown(); ImGui_ImplGlfw_Shutdown(); ImGui::DestroyContext();
    glfwDestroyWindow(window); glfwTerminate();
    return 0;
}
