# import pyrealsense2.pyrealsense2 as rs
import pyrealsense2 as rs
import numpy as np
import pickle

class DepthCamera:
    def __init__(self):
        self.pipeline = rs.pipeline()
        config = rs.config()
        with open('camera_file.txt', 'rb') as camera_file:
            global camera_info
            camera_info = pickle.load(camera_file)
        
        self.intrinsics = rs.intrinsics()
        self.intrinsics.width = camera_info.width
        self.intrinsics.height = camera_info.height
        self.intrinsics.ppx = camera_info.K[2]
        self.intrinsics.ppy = camera_info.K[5]
        self.intrinsics.fx = camera_info.K[0]
        self.intrinsics.fy = camera_info.K[4]
        self.intrinsics.model = rs.distortion.none
        self.intrinsics.coeffs = [i for i in camera_info.D]

        # pipeline and product line information to get resolution support
        pipeline_wrapper = rs.pipeline_wrapper(self.pipeline)
        self.pipeline_profile = config.resolve(pipeline_wrapper)
        device = self.pipeline_profile.get_device()
        device_product_line = str(device.get_info(rs.camera_info.product_line))
        self.depth_scale = self.pipeline_profile.get_device().first_depth_sensor().get_depth_scale()

        # point cloud initialization
        self.pointcloud = rs.pointcloud()
        align_to = rs.stream.color
        self.align = rs.align(align_to)

        # configuring the camera stream
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

        # Start streaming
        self.pipeline.start(config)


    def ssd_get_frame(self):
        frames = self.pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        depth_frame_distance = frames.get_depth_frame().as_depth_frame()
        color_image = np.asanyarray(color_frame.get_data())
        return color_image, depth_frame_distance



    def get_frame(self):
        frames = self.pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        depth_frame_distance = frames.get_depth_frame().as_depth_frame()

        # get depth information 
        self.pointcloud.map_to(depth_frame)
        points = self.pointcloud.calculate(depth_frame)

        depth_image = np.asanyarray(depth_frame.get_data())
        depth = depth_image.astype(float)
        color_image = np.asanyarray(color_frame.get_data())
        if not depth_frame or not color_frame or not points:
            return False, None, None, None
        return True, depth, color_image, points, depth_frame_distance

    def get_depth_frame(self):
        frames = self.pipeline.wait_for_frames()
        depth_frame_distance = frames.get_depth_frame().as_depth_frame()


    def get_distance(self, p0, p1):
        _, depth, color_image, points, depth_frame_distance = self.get_frame()
        distance = depth_frame_distance.get_distance(p0, p1)
        return distance

    def ssd_get_distance(self, p0, p1):
        color_image, depth_frame_distance = self.ssd_get_frame()
        distance = depth_frame_distance.get_distance(p0, p1)
        return distance

    def get_depth_coordinates(self, p0, p1):
        distance = self.get_distance(p0, p1)
        depth_coordinates =  rs.rs2_deproject_pixel_to_point(self.intrinsics, [p0, p1], distance)
        return depth_coordinates

    def ssd_get_depth_coordinates(self, p0, p1):
        distance = self.ssd_get_distance(p0, p1)
        depth_coordinates =  rs.rs2_deproject_pixel_to_point(self.intrinsics, [p0, p1], distance)
        return depth_coordinates

    def release(self):
        self.pipeline.stop()

    def get_profile(self):
        return self.pipeline_profile
    
    def get_intrinsics(self):
        return self.intrinsics
