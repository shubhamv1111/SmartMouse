import cv2
import os
import numpy as np
from PIL import Image
import mediapipe as mp
import time

colorsPath = "NavBar/Colors"
sizesPath = "NavBar/Sizes"
shapesPath = "NavBar/Shapes"
eraserPath = "NavBar/Eraser"
savePath = "NavBar/Saves"

imListColors = os.listdir(colorsPath)
imListSizes = os.listdir(sizesPath)
imListEraser = os.listdir(eraserPath)
imListSave = os.listdir(savePath)
imListShapes = os.listdir(shapesPath)

colors = []
sizes = []
eraser = []
save = []
shapes = []

navWidth = 80

def resize_image(image, width, height=navWidth):
    dim = (width, height)
    return cv2.resize(image, dim, interpolation = cv2.INTER_AREA)

# For the first 3 sets of regions
for imPath in imListColors:
    image = cv2.imread(f'{colorsPath}/{imPath}')
    image = resize_image(image, width=400)  # Resize to 384x100
    colors.append(image)

for imPath in imListSizes:
    image = cv2.imread(f'{sizesPath}/{imPath}')
    image = resize_image(image, width=240)  # Resize to 384x100
    sizes.append(image)

for imPath in imListEraser:
    image = cv2.imread(f'{eraserPath}/{imPath}')
    image = resize_image(image, width=240)  # Resize to 384x100
    eraser.append(image)
    
for imPath in imListShapes:
    image = cv2.imread(f'{shapesPath}/{imPath}')
    image = resize_image(image, width=320)  # Resize to 80x100
    shapes.append(image)

# For the last region
for imPath in imListSave:
    image = cv2.imread(f'{savePath}/{imPath}')
    image = resize_image(image, width=80)  # Resize to 128x100
    save.append(image)


def drawOnFeed(frame, canvas):
    gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
    _, ImgInv = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)
    ImgInv = cv2.cvtColor(ImgInv, cv2.COLOR_GRAY2BGR)
    frame = cv2.bitwise_and(frame, ImgInv)
    frame = cv2.bitwise_or(frame, canvas)

    return frame

class HandDetector:

    def __init__(self, mode = False, maxHands = 1, modcomplex = 1, DetectCon = 0.5, TrackCon = 0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.modcomplex = modcomplex
        self.DetectCon = DetectCon
        self.TrackCon = TrackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(self.mode, self.maxHands, self.modcomplex, self.DetectCon, self.TrackCon)
        self.mpDraw = mp.solutions.drawing_utils

    def FindHands(self, frame, draw = True):
        frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(frameRGB)

        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                
                if draw:
                    self.mpDraw.draw_landmarks(frame, handLms, self.mpHands.HAND_CONNECTIONS)

        return frame

    def FindPositions(self, frame, HandNo = 0):
        self.lm_list = []
        h, w, c = frame.shape

        if self.results.multi_hand_landmarks:

            Hand = self.results.multi_hand_landmarks[HandNo]
            for id, lm in enumerate(Hand.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                self.lm_list.append([id, cx, cy])

        return self.lm_list

    def FindGesture(self):
        fingers_id = [8, 12, 16, 20]
        fingers = []

        for id in fingers_id:
            if self.lm_list[id][2] < self.lm_list[id - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers
 
def display_navbar(colors, shapes, sizes, eraser, save):
    navbar = np.concatenate((np.repeat(colors, 1, axis=1), np.repeat(shapes, 1, axis=1), np.repeat(sizes, 1, axis=1), np.repeat(eraser, 1, axis=1), np.repeat(save, 1, axis=1)), axis=1)
    return navbar



def save_canvas(canvas, save_dir="Drawing"):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    files = os.listdir(save_dir)
    drawing_files = [f for f in files if f.startswith("drawing")]
    drawing_nums = [int(f[7:-4]) for f in drawing_files if f[7:-4].isdigit()]
    next_num = max(drawing_nums) + 1 if drawing_nums else 1

    # Create a mask of the background (black) pixels
    mask = np.all(canvas == [0, 0, 0], axis=-1)

    # Create a white image of the same size as the canvas
    white_image = np.ones_like(canvas) * 255

    # Copy the non-background pixels from the canvas to the white image
    white_image[~mask] = canvas[~mask]

    # Convert color format from BGR to RGB
    white_image = cv2.cvtColor(white_image, cv2.COLOR_BGR2RGB)

    img = Image.fromarray(white_image)
    img.save(f"{save_dir}/drawing{next_num}.png")










def main():
    width, height = 1280, 720
    brushColor = [(0, 0, 255), (0, 255, 255), (255, 0, 75), (0, 255, 0), (147, 20, 255)]  # Red, Yellow, Blue, Green, Pink
    brushSize = [8, 14, 25]
    eraserSize = [25, 45, 80]
    currColor, currShape, currBrushsize, currEraserSize, currSave = 0, 0, 1, 1, 0
    canvas = np.zeros((height, width, 3), dtype='uint8')
    canvas_prev = canvas.copy()

    cap = cv2.VideoCapture(0)
    cap.set(3, width)
    cap.set(4, height)

    drawing = False  # Flag to indicate if drawing is in progress
    start_point = None  # Starting point of the shape
    end_point = None  # Ending point of the shape
    temp_canvas = np.zeros_like(canvas)  # Temporary canvas to preview the shape
    prev_point = None  # Previous point for freehand drawing

    detector = HandDetector()

    last_save_time = time.time()
    save_triggered = False
    save_done = False

    while True:
        success, frame = cap.read()
        frame = cv2.flip(frame, 1)

        frame = detector.FindHands(frame, True)
        lm_list = detector.FindPositions(frame, 0)

        frame[0:navWidth, 0:400] = colors[currColor]
        frame[0:navWidth, 400:720] = shapes[currShape]
        frame[0:navWidth, 720:960] = sizes[currBrushsize]
        frame[0:navWidth, 960:1200] = eraser[currEraserSize]
        frame[0:navWidth, 1200:1280] = save[currSave if not save_triggered else 1]

        if len(lm_list) != 0:
            fingers = detector.FindGesture()
            xi, yi = lm_list[8][1:]
            xm, ym = lm_list[12][1:]

            if fingers[0] == 1 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0:
                if not drawing:
                    drawing = True
                    start_point = (xi, yi)
                    end_point = start_point
                    prev_point = start_point  # Initialize prev_point for freehand drawing
                    temp_canvas = np.zeros_like(canvas)  # Clear the temporary canvas
                else:
                    end_point = (xi, yi)
                    temp_canvas = np.zeros_like(canvas)  # Clear the temporary canvas

                    if currShape == 0:  # Curve
                        cv2.line(canvas, prev_point, end_point, brushColor[currColor], brushSize[currBrushsize])
                        prev_point = end_point  # Update prev_point for freehand drawing
                    elif currShape == 1:  # Rectangle
                        cv2.rectangle(temp_canvas, start_point, end_point, brushColor[currColor], brushSize[currBrushsize])
                    elif currShape == 2:  # Line
                        cv2.line(temp_canvas, start_point, end_point, brushColor[currColor], brushSize[currBrushsize])
                    elif currShape == 3:  # Oval
                        cv2.ellipse(temp_canvas, ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2), (abs(start_point[0] - end_point[0]) // 2, abs(start_point[1] - end_point[1]) // 2), 0, 0, 360, brushColor[currColor], brushSize[currBrushsize])

                    if currShape != 0:
                        frame = cv2.bitwise_or(frame, temp_canvas)

            elif fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0:
                drawing = False
                start_point = None
                end_point = None
                if currShape != 0:
                    # Create a mask of the shape
                    shape_mask = cv2.inRange(temp_canvas, brushColor[currColor], brushColor[currColor])
                    # Bitwise AND the mask with the main canvas to "erase" the area where you want to draw the shape
                    canvas = cv2.bitwise_and(canvas, canvas, mask=cv2.bitwise_not(shape_mask))
                    # Bitwise OR the result with the temporary canvas to "draw" the shape on the erased area
                    canvas = cv2.bitwise_or(canvas, temp_canvas)
                temp_canvas = np.zeros_like(canvas)  # Clear the temporary canvas

                if ym < navWidth:
                    region = xm // 80  # Divide the navbar into 16 regions of 80px each

                    if region < 5:  # First 5 regions for color
                        currColor = region
                    elif region < 9:  # Next 4 regions for shapes
                        currShape = region - 5
                    elif region < 12:  # Next 3 regions for size
                        currBrushsize = region - 9
                    elif region < 15:  # Next 3 regions for eraser
                        currEraserSize = region - 12
                    else:  # Last region for save
                        if not save_triggered and not save_done and not np.array_equal(canvas, canvas_prev):
                            save_canvas(canvas)
                            save_triggered = True
                            last_save_time = time.time()
                            save_done = True
                            canvas_prev = canvas.copy()

            elif fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1:
                cv2.circle(frame, (xm, ym), eraserSize[currEraserSize], (255, 255, 255), -1)
                cv2.circle(canvas, (xm, ym), eraserSize[currEraserSize], (0, 0, 0), -1)
                drawing = False
                start_point = None
                end_point = None
                prev_point = None  # Reset prev_point for freehand drawing
                temp_canvas = np.zeros_like(canvas)  # Clear the temporary canvas

            else:
                drawing = False
                start_point = None
                end_point = None
                prev_point = None  # Reset prev_point for freehand drawing
                temp_canvas = np.zeros_like(canvas)  # Clear the temporary canvas
                if save_triggered:
                    save_done = False

        if save_triggered and time.time() - last_save_time > 1:
            save_triggered = False

        if not save_triggered and save_done:
            currSave = 0
            save_done = False

        frame = drawOnFeed(frame, canvas)
        # Draw the temporary shape on top of the existing shapes
        if temp_canvas.any():
            frame = cv2.bitwise_or(frame, temp_canvas)
        cv2.imshow('Smart Board', frame)

        if cv2.waitKey(20) & 0xFF == ord('x'):
            break

    cv2.destroyAllWindows()
    cap.release()

if __name__ == "__main__":
    main()

