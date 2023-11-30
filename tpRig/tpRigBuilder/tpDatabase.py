import numpy as np

class Database:

    def __init__(self):

        self.database_name = ''
        self.geometry_beauty = ''
        self.geometry_system = ''
        self.joint_bind = []
        self.top_group = ''
        self.fk_top = ''
        self.fk_bottom = ''

        self.dict_data_slot = {}
        self.list_data_slot = []

    def add_module_slot(self, module):
        self.dict_data_slot.update({module: {}})

    def module_add_data(self, module, data):
        self.dict_data_slot.update({module: data})



class DatabaseManager:

    def __init__(self):
        pass

    def export_database(self):
        pass

    def import_database(self):
        pass

    def add_module(self, module_name):
        pass

# # Camera positions (your camera positions in 3D space)
# camera_positions = np.array([
#     [1.0, 0.0, 0.0],  # Camera 1
#     [0.0, 1.0, 0.0],  # Camera 2
#     [0.0, 0.0, 1.0]   # Camera 3
# ])
#
# # Estimated 3D joint positions (from machine vision)
# estimated_positions = np.array([
#     [1.0, 2.0],  # Joint position in Camera 1
#     [2.0, 1.0],  # Joint position in Camera 2
#     [1.0, 1.0]   # Joint position in Camera 3
# ])
#
# # Gradient Descent to minimize the distance
# common_point = np.zeros((3, 2))  # Initialize common point
# learning_rate = 0.01
# iterations = 100
#
# for _ in range(iterations):
#     # Calculate the cost (distance) between estimated positions and common point
#     cost = np.sum(np.linalg.norm(estimated_positions - common_point, axis=1))
#
#     # Calculate the gradient of the cost
#     gradient = np.sum((common_point - estimated_positions), axis=0)
#
#     # Update the common point using gradient descent
#     common_point -= learning_rate * gradient
#
# print("Optimized Common 3D Point:", common_point)
#
#
# def find_closes_distance():
#     loc_a = ''
#     loc_b = ''
#
#     # store camera position
#     # bring in image place
#     # camera fit view
#     # group camera - add image place
#     # send camera back to stored position
#     # image on image plane should now perfectly align with the 3d object
