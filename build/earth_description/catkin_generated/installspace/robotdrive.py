import rospy
import math
from std_msgs.msg import String
from geometry_msgs.msg import Twist
#Use dictionary type to store the key-value mapping relationship between letters and speed commands, the default linear velocity is 1m/s, and the default angular velocity is 1rad/s.
key_mapping = { 'w': [ 0, 1], 'x': [ 0, -1], 
                'a': [ 1, 0], 'd': [-1,  0], 
                's': [ 0, 0] }
g_twist_pub = None
g_target_twist = None 
g_last_twist = None
g_last_send_time = None
 #Accept the speed range specified by the user, default 0.1, low speed operation
g_vel_scales = [0.1, 0.1] 
 #Accept the linear acceleration and angular acceleration specified by the user (the default value is 1)
g_vel_ramps = [1, 1]
 
 #Limit speed function
def ramped_vel(v_prev, v_target, t_prev, t_now, ramp_rate):
     #Declare acceleration
  step = ramp_rate * (t_now - t_prev).to_sec()
     #Judge acceleration/deceleration  
  sign = 1.0 if (v_target > v_prev) else -1.0
     #Speed ​​variable (target speed—current speed)
  error = math.fabs(v_target - v_prev)
     #Speed ​​variable is less than acceleration
  if error < step: 
         #Directly return to target speed
    return v_target
  else:
         #Otherwise increase or decrease the acceleration by one unit
    return v_prev + sign * step 
 
 
 
 #Speed ​​parameterization
def ramped_twist(prev, target, t_prev, t_now, ramps):
     #Message Statement
  tw = Twist()
     #Modify the angular velocity value according to the angular acceleration
  tw.angular.z = ramped_vel(prev.angular.z, target.angular.z, t_prev,
                            t_now, ramps[0])
 
     #Modify the linear velocity value according to the linear acceleration
  tw.linear.x = ramped_vel(prev.linear.x, target.linear.x, t_prev,
                           t_now, ramps[1])
  return tw
 
 
 
 #Send Twist speed command message
def send_twist():
  global g_last_twist_send_time, g_target_twist, g_last_twist,\
         g_vel_scales, g_vel_ramps, g_twist_pub
     #Get the current time of the system
  t_now = rospy.Time.now()
     #Parameterized modification speed
  g_last_twist = ramped_twist(g_last_twist, g_target_twist,
                              g_last_twist_send_time, t_now, g_vel_ramps)
  g_last_twist_send_time = t_now
     #Send the final parameterized modified speed command message
  g_twist_pub.publish(g_last_twist)
 
 
 
 #Accept keyboard commands
def keys_cb(msg):
  global g_target_twist, g_last_twist, g_vel_scales
     #Determine whether the input is a valid command
  if len(msg.data) == 0 or not key_mapping.has_key(msg.data[0]):
    return 
     #Get the speed value in the keys message
  vels = key_mapping[msg.data[0]]
     #Speed ​​parameterization to meet different speed requirements, the default is 0.1 of the input speed
  g_target_twist.angular.z = vels[0] * g_vel_scales[0]
  g_target_twist.linear.x  = vels[1] * g_vel_scales[1]
 
 
 
 #Get the speed range parameters and acceleration entered by the user, and return to the default value without maturity
def fetch_param(name, default):
  if rospy.has_param(name):
    return rospy.get_param(name)
  else:
    print "parameter [%s] not defined. Defaulting to %.3f" % (name, default)
    return default
 
if __name__ == '__main__':
     #Node Initialization
  rospy.init_node('keys_to_twist')
     #Get the current time of the system
  g_last_twist_send_time = rospy.Time.now()
     #Post speed command message
  g_twist_pub = rospy.Publisher('cmd_vel', Twist, queue_size=1)
     #Subscribe to keys news
  rospy.Subscriber('keys', String, keys_cb)
     #Declare Twist message type
  g_target_twist = Twist() 
  g_last_twist = Twist()
     #Get the parameters entered by the user
  g_vel_scales[0] = fetch_param('~angular_scale', 0.1)
  g_vel_scales[1] = fetch_param('~linear_scale', 0.1)
  g_vel_ramps[0] = fetch_param('~angular_accel', 1.0)
  g_vel_ramps[1] = fetch_param('~linear_accel', 1.0)
 
  rate = rospy.Rate(20)
  while not rospy.is_shutdown():
    send_twist()
    rate.sleep()
