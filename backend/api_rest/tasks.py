# import serial
# from celery import shared_task

# @shared_task
# def listen_sensor_and_play_audio():
#     print("Task bắt đầu lắng nghe dữ liệu.")
    
#     # Giả sử bạn sử dụng serial port để đọc dữ liệu từ RS-485
#     ser = serial.Serial('/dev/ttyUSB0', 9600)

#     while True:
#         if ser.in_waiting > 0:
#             data = ser.readline().decode('utf-8').strip()
            
            
