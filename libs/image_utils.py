import cv2


def extractAndRotateImage(img, rect, interpolation=cv2.INTER_CUBIC):
    """
    Extracts and rectifies a rotated bounding box from an image.

    This function takes an image and an oriented bounding box (OBB), rotates the 
    image such that the bounding box becomes axis-aligned (rectangular), and then 
    crops the bounding box area.

    Args:
        img (numpy.ndarray): The input image from which the bounding box is extracted.
        rect (tuple): The oriented bounding box parameters.
                     - rect[0]: Center coordinates of the bounding box (x, y).
                     - rect[1]: Size of the bounding box (width, height).
                     - rect[2]: Rotation angle of the bounding box (in degrees).
        interpolation (int, optional): Interpolation method used when rotating the image.
                                       Defaults to cv2.INTER_CUBIC.

    Returns:
        cropped_image (numpy.ndarray): The cropped rectangle region from the rotated image.
    """

    # Process:
    #    1. Extracts the center, size, and angle of the bounding box.
    #    2. Computes a rotation matrix to align the bounding box with the image axes.
    #    3. Rotates the image based on the calculated rotation matrix.
    #    4. Crops the now axis-aligned bounding box from the rotated image.


    # get the parameter of the small rectangle
    center, size, angle = rect[0], rect[1], rect[2]
    center, size = tuple(map(int, center)), tuple(map(int, size))

    # get row and col num in img
    height, width = img.shape[0], img.shape[1]

    # calculate the rotation matrix
    M = cv2.getRotationMatrix2D(center, angle, 1)
    # rotate the original image
    img_rot = cv2.warpAffine(img, M, (width, height), flags=interpolation)

    # now rotated rectangle becomes vertical, and we crop it
    img_crop = cv2.getRectSubPix(img_rot, size, center)
    return img_crop


def prepare_for_ocr(img):
    """
    Processes a cropped rectangle for OCR detection by ensuring the image is wider than tall
    and generating both the original (or rotated) and a 180-degree rotated variant.
    
    Args:
        img (numpy.ndarray): The cropped rectangle image.

    Returns:
        tuple: (processed_img, rotated_180_img)
               - processed_img: Image oriented to be wider than tall.
               - rotated_180_img: 180-degree rotated version of `processed_img`.
    """
    # Get image dimensions
    height, width = img.shape[:2]

    # Rotate 90 degrees clockwise if the image is taller than it is wide
    if height > width:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)

    # Generate the 180-degree rotated image
    rotated_180_img = cv2.rotate(img, cv2.ROTATE_180)

    return img, rotated_180_img


def cropImage(frame, box):
    """
    Crop the image based on the bounding box coordinates.

    :param frame: Input image.
    :param box: Tuple or list containing (start_x, start_y, end_x, end_y).
    :return: Cropped image.
    """
    start_x, start_y, end_x, end_y = box
    return frame[start_y:end_y, start_x:end_x]

def grayscale(image):
    """
    Convert image to grayscale.
    """
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

def denoise(image):
    """
    Apply median blur to the image to remove noise.
    """
    return cv2.medianBlur(image, 5)

def thresholding(image):
    """
    Apply Otsu's thresholding to the image.
    """
    return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
