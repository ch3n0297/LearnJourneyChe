import open3d as o3d
import numpy as np

# ---------------------- 定义点云体素化函数 ----------------------
def get_mesh(_relative_path):
    mesh = o3d.io.read_triangle_mesh(_relative_path)
    mesh.compute_vertex_normals()
    return mesh
# =============================================================

# ------------------------- Ball pivoting --------------------------
print("->Ball pivoting...")
_relative_path = o3d.data.BunnyMesh().path    # 设置相对路径
N = 2000                        # 将点划分为N个体素
pcd = get_mesh(_relative_path).sample_points_poisson_disk(N)
o3d.visualization.draw_geometries([pcd])

radii = [0.005, 0.01, 0.02, 0.04]
rec_mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(pcd, o3d.utility.DoubleVector(radii))
o3d.visualization.draw_geometries([pcd, rec_mesh])