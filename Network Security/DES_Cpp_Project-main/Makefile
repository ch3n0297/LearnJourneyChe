# ==== Platform detection ====
ifeq ($(OS),Windows_NT)
    PLATFORM := Windows
else
    UNAME_S := $(shell uname -s)
    ifeq ($(UNAME_S),Darwin)
        PLATFORM := macOS
    else
        PLATFORM := Linux
    endif
endif

.DEFAULT_GOAL := help
CXX ?= clang++

# ==== Common compiler flags ====
CXXFLAGS_COMMON = -std=c++17 -g \
                  -Iinclude \
                  -Ithird_party/imgui \
                  -Ithird_party/imgui/backends \
                  -Ithird_party/tinyfiledialogs

ifeq ($(PLATFORM),macOS)
    CXXFLAGS = $(CXXFLAGS_COMMON) -I/opt/homebrew/include -DGL_SILENCE_DEPRECATION
    LDFLAGS  = -L/opt/homebrew/lib -lglfw \
               -framework Cocoa -framework OpenGL -framework IOKit -framework CoreVideo
else ifeq ($(PLATFORM),Windows)
    CXXFLAGS = $(CXXFLAGS_COMMON)
    LDFLAGS  = -lglfw3 -lopengl32 -lgdi32 -lole32 -luuid -lcomdlg32 -static
else
    CXXFLAGS = $(CXXFLAGS_COMMON) -pthread
    LDFLAGS  = -lglfw -lGL -lX11 -lpthread -ldl
endif

# ==== CLI tools ====
CLI_TOOLS := letter_freq block_sub_cipher rsa_fast_exp hill_cipher
CLI_BINS  := $(patsubst %,dist/%,$(CLI_TOOLS))

dist/%: src/%.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) $< -o $@

# ==== GUI ====
SRCS = src/gui_main.cpp src/des.cpp \
       third_party/imgui/imgui.cpp \
       third_party/imgui/imgui_draw.cpp \
       third_party/imgui/imgui_widgets.cpp \
       third_party/imgui/imgui_tables.cpp \
       third_party/imgui/imgui_demo.cpp \
       third_party/imgui/backends/imgui_impl_glfw.cpp \
       third_party/imgui/backends/imgui_impl_opengl3.cpp \
       third_party/tinyfiledialogs/tinyfiledialogs.c
TARGET = dist/des_gui_app

$(TARGET): $(SRCS)
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) $^ $(LDFLAGS) -o $@

# ==== Phony targets ====
.PHONY: all clean run help package

all: $(TARGET) $(CLI_BINS)

clean:
	rm -rf dist/*

run: $(TARGET)
	@echo "Launching DES GUI..."
	@$(TARGET)

help:
	@echo ""
	@echo "DES Project – Makefile"
	@echo "----------------------"
	@echo "make / make all      → Build GUI + 4 CLI tools"
	@echo "make run             → Build (if needed) and launch GUI"
	@echo "make dist/<tool>     → Build single CLI tool, e.g. 'make dist/letter_freq'"
	@echo "make clean           → Remove build artifacts"
	@echo "make package         → Platform-specific archive/bundle"
	@echo ""

# （package 區段保留原樣，略）
