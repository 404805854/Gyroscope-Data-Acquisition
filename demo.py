import cv2
from controller import Gyros
import argparse
import datetime
import keyboard
from loguru import logger
import concurrent.futures
import time

WIDTH = 1280
HEIGHT = 720
FPS = 12.0


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--align", type=str,
                        required=False, default="align.mp4")
    now = datetime.datetime.now()
    parser.add_argument("-v", "--video", type=str,
                        required=False, default=f"{now.year}-{now.month}-{now.day}.mp4")
    parser.add_argument("-d", "--data", type=str,
                        required=False, default="data.txt")
    args = parser.parse_args()

    return args


def gyros_process() -> list:
    gyros = Gyros()
    gyros.start()
    ret = []
    if not gyros.check():
        print(gyros._get_port_list())
        exit()
    while True:
        if keyboard.is_pressed("esc"):
            break
        ret.append((time.time(), gyros.get()))
    return ret


def video_process() -> list:
    time.sleep(1)
    data = []
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, FPS)
    while True:
        if keyboard.is_pressed("esc"):
            break
        ret, frame = cap.read()
        if ret:
            data.append((time.time(), frame))
    cap.release()
    return data


def align(align, gyros_data, image_data) -> None:
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    ofile = cv2.VideoWriter(align, fourcc, FPS, (WIDTH, HEIGHT))
    pos = 0
    for data in image_data:
        timestamp = data[0]
        image = data[1]
        for i in range(pos, len(gyros_data)):
            if gyros_data[i][0] < timestamp:
                continue
            elif gyros_data[i][0] == timestamp:
                pos = i
                break
            else:
                if i > 0:
                    pos = i - 1
                else:
                    pos = i
                break
        logger.debug(f"timestamp {timestamp} - {gyros_data[pos][0]}")
        cv2.putText(image, str(gyros_data[pos][1]),
                    (0, 50), cv2.FONT_ITALIC, 2, (0, 0, 0))
        ofile.write(image)
    ofile.release()


def main():
    args = parse_args()
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        video_future = executor.submit(video_process)
        gyros_data = gyros_process()
        image_data = video_future.result()

    align(args.align, gyros_data, image_data)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    ofile = cv2.VideoWriter(args.video, fourcc, FPS, (WIDTH, HEIGHT))
    for data in image_data:
        ofile.write(data[1])
    ofile.release()
    with open(args.data, "w", encoding="utf8") as ofile:
        for data in gyros_data:
            ofile.write(str(data[0])+" : "+str(data[1])+"\n")


if __name__ == "__main__":
    main()
