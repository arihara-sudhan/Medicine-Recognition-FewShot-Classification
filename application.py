import cv2
import torch
import pickle
from tripletclass import Model
from PIL import Image
import os
import json
from tts import speak

with open('meta/meta.json') as f:
    data = json.load(f)


# Set environment variable to suppress OpenMP warning
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Load index and train labels
with open('./Index/data.pickle', 'rb') as f:
    index, train_labels = pickle.load(f)

# Function to get image embedding
def get_image_embedding(image_path, device=torch.device("cpu")):
    image = Image.open(image_path).convert('RGB')
    image = Model.transform(image).unsqueeze(0).to(device)
    with torch.no_grad():
        embedding = Model.model(image)
    return embedding

# Function to find nearest neighbor
def find_nearest_neighbor(embedding):
    _, nearest_index = index.search(embedding.view(1, -1), 1)
    return train_labels[nearest_index.item()][0]

# Main function
def main():
    # Open the default camera (index 0)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Unable to open camera.")
        return

    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        if ret:
            # Display the captured frame
            cv2.imshow('SHOW THE TABLET AND CLICK ENTER', frame)

            # Check for key press events
            key = cv2.waitKey(1)
            if key == 13:  # 13 is the ASCII code for the return key
                # Save the current frame as "frame.jpg"
                cv2.imwrite("./imgs/frame.jpg", frame)
                embedding = get_image_embedding("./imgs/frame.jpg")
                label = find_nearest_neighbor(embedding)
                print(label)
                speak(data.get(label))

            elif key == 27:  # 27 is the ASCII code for the Escape key
                break
        else:
            print("Error: Unable to capture frame.")

    # Release the camera and close all OpenCV windows
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()



