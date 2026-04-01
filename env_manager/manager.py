import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped, PoseStamped
from nav_msgs.msg import Odometry
import threading
import time
import csv
import os
import math

class EnvManager(Node):
    def __init__(self):
        super().__init__('env_manager')

        # --- Logging Setup ---
        self.log_dir = 'log'
        self.log_file = os.path.join(self.log_dir, 'race_insights.csv')
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        with open(self.log_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'ego_x', 'ego_y', 'opp_x', 'opp_y', 'distance', 'ego_speed', 'opp_speed'])

        # --- Publishers & Subscribers ---
        self.ego_reset_pub = self.create_publisher(PoseWithCovarianceStamped, '/initialpose', 10)
        self.opp_reset_pub = self.create_publisher(PoseStamped, '/goal_pose', 10)
        self.create_subscription(Odometry, '/ego_racecar/odom', self.ego_odom_cb, 10)
        self.create_subscription(Odometry, '/opp_racecar/odom', self.opp_odom_cb, 10)

        # --- State Variables ---
        self.ego_pose = [0.0, 0.0]
        self.opp_pose = [0.0, 0.0]
        self.ego_v, self.opp_v = 0.0, 0.0
        self.ego_last_x, self.opp_last_x = 0.0, 0.0
        self.ego_start_time, self.opp_start_time = None, None

        # --- Racing Metrics ---
        self.ego_laps = 0
        self.opp_laps = 0
        self.ego_laps_led = 0
        self.lap_winners = {}  # lap_number -> 'EGO' or 'OPP'

        # --- Threads & Timers ---
        self.thread = threading.Thread(target=self.keyboard_listener, daemon=True)
        self.thread.start()
        self.create_timer(0.05, self.log_to_csv)
        
        self.get_logger().info("Env Manager Initialized. Press 'r' + Enter to reset.")

    def log_to_csv(self):
        dist = math.sqrt((self.ego_pose[0] - self.opp_pose[0])**2 + (self.ego_pose[1] - self.opp_pose[1])**2)
        timestamp = self.get_clock().now().nanoseconds / 1e9
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, self.ego_pose[0], self.ego_pose[1], self.opp_pose[0], self.opp_pose[1], dist, self.ego_v, self.opp_v])

    def keyboard_listener(self):
        while rclpy.ok():
            try:
                user_input = input().strip().lower()
                if user_input == 'r': self.reset_cars()
                elif user_input == 'q': rclpy.shutdown()
            except Exception as e: self.get_logger().warning(f"Keyboard error: {e}")

    def reset_cars(self):
        self.get_logger().info("Resetting cars and metrics...")
        now = self.get_clock().now().nanoseconds / 1e9
        
        # Reset Files and State
        with open(self.log_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'ego_x', 'ego_y', 'opp_x', 'opp_y', 'distance', 'ego_speed', 'opp_speed'])

        self.ego_laps, self.opp_laps, self.ego_laps_led = 0, 0, 0
        self.lap_winners = {}
        self.ego_start_time, self.opp_start_time = now, now
        self.ego_last_x, self.opp_last_x = 0.0, 0.0

        # Teleport
        ego_msg = PoseWithCovarianceStamped()
        ego_msg.header.frame_id = 'map'
        ego_msg.pose.pose.position.x, ego_msg.pose.pose.position.y = 0.0, 0.0
        ego_msg.pose.pose.orientation.w = 1.0
        self.ego_reset_pub.publish(ego_msg)

        opp_msg = PoseStamped()
        opp_msg.header.frame_id = 'map'
        opp_msg.pose.position.x, opp_msg.pose.position.y = 0.7, 0.7
        opp_msg.pose.orientation.w = 1.0
        self.opp_reset_pub.publish(opp_msg)

    def check_lap_status(self, car_label, curr_x, last_x, start_time):
        updated_start_time = start_time
        if last_x < 0 and curr_x >= 0:
            now = self.get_clock().now().nanoseconds / 1e9
            if start_time:
                # Increment internal lap counter
                if car_label == "EGO":
                    self.ego_laps += 1
                    current_lap_num = self.ego_laps
                else:
                    self.opp_laps += 1
                    current_lap_num = self.opp_laps

                # Determine if this car led this lap
                if current_lap_num not in self.lap_winners:
                    self.lap_winners[current_lap_num] = car_label
                    if car_label == "EGO":
                        self.ego_laps_led += 1
                
                # Report Metrics
                self.get_logger().info(f"--- {car_label} Finished Lap {current_lap_num} ---")
                self.get_logger().info(f"Stats: Ego Laps: {self.ego_laps} | Opp Laps: {self.opp_laps} | Ego Laps Led: {self.ego_laps_led}")
                self.get_logger().info(f"------------------------------------------------")

            updated_start_time = now
        return updated_start_time, curr_x

    def ego_odom_cb(self, msg):
        self.ego_pose = [msg.pose.pose.position.x, msg.pose.pose.position.y]
        self.ego_v = msg.twist.twist.linear.x
        self.ego_start_time, self.ego_last_x = self.check_lap_status("EGO", self.ego_pose[0], self.ego_last_x, self.ego_start_time)

    def opp_odom_cb(self, msg):
        self.opp_pose = [msg.pose.pose.position.x, msg.pose.pose.position.y]
        self.opp_v = msg.twist.twist.linear.x
        self.opp_start_time, self.opp_last_x = self.check_lap_status("OPP", self.opp_pose[0], self.opp_last_x, self.opp_start_time)

def main(args=None):
    rclpy.init(args=args)
    node = EnvManager()
    try: rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException): pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()