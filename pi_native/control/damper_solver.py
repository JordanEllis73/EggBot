import numpy as np


class DamperMechanism:

    servo_arm_length: float = 0.035
    middle_joint_length: float = 0.059
    damper_arm_length: float = 0.07
    servo_offset: float = 0.01
    servo_to_center: float = 0.08440972
    damper_min_ang: float = 0.523599 # radians
    damper_max_ang: float = 1.0472 # radians

    eps: float = 1e-3

    def compute_servo_ang(self, desired_damper_perc: float):
        desired_ang = 0.01*desired_damper_perc*(self.damper_max_ang - self.damper_min_ang) + self.damper_min_ang

        servo_min_ang = np.deg2rad(-30)
        servo_max_ang = np.deg2rad(42)

        # init_guess = (servo_max_ang + servo_min_ang) / 2.0
        i = 0
        best_val = 1000000000
        best_ang = None
        for init_guess in np.arange(servo_min_ang, servo_max_ang, 0.001):
            val = self._linkage_kinematics(
                self.servo_arm_length,
                self.middle_joint_length,
                self.damper_arm_length,
                self.servo_offset,
                self.servo_to_center,
                init_guess,
                desired_ang)
            print(f"output: {val}")
            if val < best_val:
                best_val = val
                best_ang = init_guess
            # if abs(val) < self.eps:
            #     break
            #
            # if val < 0:
            #     init_guess = (servo_min_ang + init_guess) / 2
            # elif val > 0:
            #     init_guess = (servo_max_ang + init_guess) / 2
            # i += 1
            # if i > 10:
            #     break

        return best_ang 

    def _linkage_kinematics(self, a, b, c, d, h, input_ang, output_ang):
        # return output corresponding to how much constraint is violated
        c1 = (b*b - (h - a*np.cos(input_ang) - c*np.cos(output_ang))**2)
        return d + a*np.sin(input_ang) + c*np.sin(output_ang) + b + np.sqrt(c1)
        
if __name__ == "__main__":
    damper = DamperMechanism()
    # print(damper.compute_servo_ang(80))
    print(np.rad2deg(damper.compute_servo_ang(50)))
