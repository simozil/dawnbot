import ast
import json
import re
import requests
import random
import time
import datetime
import urllib3
from PIL import Image
import base64
from io import BytesIO
import ddddocr
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from loguru import logger

KeepAliveURL = "https://www.aeropres.in/chromeapi/dawn/v1/userreward/keepalive"
GetPointURL = "https://www.aeropres.in/api/atom/v1/userreferral/getpoint"
LoginURL = "https://www.aeropres.in//chromeapi/dawn/v1/user/login/v2"
PuzzleID = "https://www.aeropres.in/chromeapi/dawn/v1/puzzle/get-puzzle"

# Create a request session
session = requests.Session()

# Set common request headers
headers = {
    "Content-Type": "application/json",
    "Origin": "chrome-extension://fpdkjdnhkakefebpekbdhillbhonfjjp",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Priority": "u=1, i",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
}

def GetPuzzleID():
    r = session.get(PuzzleID, headers=headers, verify=False).json()
    puzzid = r['puzzle_id']
    return puzzid

# Check if the CAPTCHA expression is valid
def IsValidExpression(expression):
    # Update regex pattern to allow letters, numbers, and common math symbols
    pattern = r'^[A-Za-z0-9\+\-\*/]{6}$'
    if re.match(pattern, expression):
        return True
    return False

# CAPTCHA recognition
def RemixCaptacha(base64_image):
    # Decode the Base64 string into binary data
    image_data = base64.b64decode(base64_image)
    # Use BytesIO to convert the binary data into a readable file object
    image = Image.open(BytesIO(image_data))

    # Convert the image to RGB mode
    image = image.convert('RGB')
    # Create a new image (white background)
    new_image = Image.new('RGB', image.size, 'white')
    # Get the image width and height
    width, height = image.size
    # Loop through all the pixels
    for x in range(width):
        for y in range(height):
            pixel = image.getpixel((x, y))
            # If the pixel is black, keep it; otherwise, set it to white
            if pixel == (48, 48, 48):  # Black pixel
                new_image.putpixel((x, y), pixel)  # Keep original black
            else:
                new_image.putpixel((x, y), (255, 255, 255))  # Replace with white

    # Create an OCR object
    ocr = ddddocr.DdddOcr(show_ad=False)
    ocr.set_ranges(0)  # Set OCR recognition range to include more symbols
    result = ocr.classification(new_image)
    logger.debug(f'[1] CAPTCHA recognition result: {result}, Is it a valid CAPTCHA {IsValidExpression(result)}')

    if IsValidExpression(result):
        return result
    return None

# Login function
def login(USERNAME, PASSWORD):
    puzzid = GetPuzzleID()
    current_time = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds').replace("+00:00", "Z")
    data = {
        "username": USERNAME,
        "password": PASSWORD,
        "logindata": {
            "_v": "1.0.7",
            "datetime": current_time
        },
        "puzzle_id": puzzid,
        "ans": "0"
    }

    # CAPTCHA recognition part
    refresh_image = session.get(f'https://www.aeropres.in/chromeapi/dawn/v1/puzzle/get-puzzle-image?puzzle_id={puzzid}', headers=headers, verify=False).json()
    code = RemixCaptacha(refresh_image['imgBase64'])
    
    if code:
        logger.success(f'[√] Successfully obtained CAPTCHA result {code}')
        data['ans'] = str(code)
        login_data = json.dumps(data)
        logger.info(f'[2] Login data: {login_data}')
        try:
            r = session.post(LoginURL, login_data, headers=headers, verify=False).json()
            logger.debug(r)
            token = r['data']['token']
            logger.success(f'[√] Successfully obtained AuthToken {token}')
            return token
        except Exception as e:
            logger.error(f'[x] Login failed, error: {e}')
            return None
    return None

# Keep the session alive
def KeepAlive(USERNAME, TOKEN):
    data = {
        "username": USERNAME,
        "extensionid": "fpdkjdnhkakefebpekbdhillbhonfjjp",
        "numberoftabs": 0,
        "_v": "1.0.7"
    }
    json_data = json.dumps(data)
    headers['authorization'] = "Bearer " + str(TOKEN)
    r = session.post(KeepAliveURL, data=json_data, headers=headers, verify=False).json()
    logger.info(f'[3] Keeping the connection alive... {r}')

# Get points
def GetPoint(TOKEN):
    headers['authorization'] = "Bearer " + str(TOKEN)
    r = session.get(GetPointURL, headers=headers, verify=False).json()
    logger.success(f'[√] Successfully obtained points {r}')

# Main function
def main(USERNAME, PASSWORD):
    TOKEN = ''
    if TOKEN == '':
        while True:
            TOKEN = login(USERNAME, PASSWORD)
            if TOKEN:
                break
    # Initialize counter
    count = 0
    max_count = 200  # Re-obtain the TOKEN after running 200 times
    while True:
        try:
            # Perform KeepAlive and GetPoint actions
            KeepAlive(USERNAME, TOKEN)
            GetPoint(TOKEN)
            # Update the counter
            count += 1
            # Re-obtain the TOKEN after max_count times
            if count >= max_count:
                logger.debug(f'[√] Re-login to obtain Token...')
                while True:
                    TOKEN = login(USERNAME, PASSWORD)
                    if TOKEN:
                        break
                count = 0  # Reset the counter
        except Exception as e:
            logger.error(e)

if __name__ == '__main__':
    with open('password.txt', 'r') as f:
        username, password = f.readline().strip().split(':')
    main(username, password)
