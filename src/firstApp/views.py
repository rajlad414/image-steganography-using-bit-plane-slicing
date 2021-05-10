from django.shortcuts import render
from django.core.files.storage import FileSystemStorage

import os, sys
from PIL import Image
import cv2

# Create your views here.
def encode(img_visible, img_hidden):
    visible_image_copy = img_visible.load()
    img_hidden_copy = img_hidden.load()
    width_visible, height_visible = img_visible.size
    width_hidden, height_hidden = img_hidden.size
    hidden_image_pixels = get_binary_pixel_values(img_hidden_copy, width_hidden, height_hidden)
    encoded_image = change_binary_values(visible_image_copy, hidden_image_pixels, width_visible, height_visible, width_hidden, height_hidden)
    return img_visible

def get_binary_pixel_values(img, width, height):
    hidden_image_pixels = ''
    for col in range(width):
        for row in range(height):
            pixel = img[col, row]
            r = pixel[0]
            g = pixel[1]
            b = pixel[2]
            r_binary, g_binary, b_binary = rgb_to_binary(r, g, b)
            hidden_image_pixels += r_binary + g_binary + b_binary
    return hidden_image_pixels

def change_binary_values(img_visible, hidden_image_pixels, width_visible, height_visible, width_hidden, height_hidden):
    idx = 0
    for col in range(width_visible):
            for row in range(height_visible):
                if row == 0 and col == 0:
                    width_hidden_binary = add_leading_zeros(bin(width_hidden)[2:], 12)
                    height_hidden_binary = add_leading_zeros(bin(height_hidden)[2:], 12)
                    w_h_binary = width_hidden_binary + height_hidden_binary
                    img_visible[col, row] = (int(w_h_binary[0:8], 2), int(w_h_binary[8:16], 2), int(w_h_binary[16:24], 2))
                    continue
                r, g, b = img_visible[col, row]
                r_binary, g_binary, b_binary = rgb_to_binary(r, g, b)
                r_binary = r_binary[0:4] + hidden_image_pixels[idx:idx+4]
                g_binary = g_binary[0:4] + hidden_image_pixels[idx+4:idx+8]
                b_binary = b_binary[0:4] + hidden_image_pixels[idx+8:idx+12]
                idx += 12
                img_visible[col, row] = (int(r_binary, 2), int(g_binary, 2), int(b_binary, 2))
                if idx >= len(hidden_image_pixels):
                    return img_visible
        # can never be reached, but let's return the image anyway
    return img_visible

def add_leading_zeros(binary_number, expected_length):
    length = len(binary_number)
    return (expected_length - length) * '0' + binary_number

def rgb_to_binary(r, g, b):
    return add_leading_zeros(bin(r)[2:], 8), add_leading_zeros(bin(g)[2:], 8), add_leading_zeros(bin(b)[2:], 8)

def decode(image):
    image_copy = image.load()
    width_visible, height_visible = image.size
    r, g, b = image_copy[0, 0]
    r_binary, g_binary, b_binary = rgb_to_binary(r, g, b)
    w_h_binary = r_binary + g_binary + b_binary
    width_hidden = int(w_h_binary[0:12], 2)
    height_hidden = int(w_h_binary[12:24], 2)
    pixel_count = width_hidden * height_hidden
    hidden_image_pixels = extract_hidden_pixels(image_copy, width_visible, height_visible, pixel_count)
    decoded_image = reconstruct_image(hidden_image_pixels, width_hidden, height_hidden)
    return decoded_image

def extract_hidden_pixels(image, width_visible, height_visible, pixel_count):
    hidden_image_pixels = ''
    idx = 0
    for col in range(width_visible):
        for row in range(height_visible):
            if row == 0 and col == 0:
                continue
            r, g, b = image[col, row]
            r_binary, g_binary, b_binary = rgb_to_binary(r, g, b)
            hidden_image_pixels += r_binary[4:8] + g_binary[4:8] + b_binary[4:8]
            if idx >= pixel_count * 2:
                return hidden_image_pixels
    return hidden_image_pixels

def reconstruct_image(image_pixels, width, height):
    image = Image.new("RGB", (width, height))
    image_copy = image.load()
    idx = 0
    for col in range(width):
        for row in range(height):
            r_binary = image_pixels[idx:idx+8]
            g_binary = image_pixels[idx+8:idx+16]
            b_binary = image_pixels[idx+16:idx+24]
            image_copy[col, row] = (int(r_binary, 2), int(g_binary, 2), int(b_binary, 2))
            idx += 24
    return image


def index(request):
    cover="./media/extra images/cover.jpg"
    hide="./media/extra images/hidding.jpg"
    output_path="./media/extra images/encrypted.jpg"
    encodee="./media/extra images/encrypted.jpg"
    decode_path="./media/extra images/decrypted.jpg"
    context={
        'cover':cover,
        'hide':hide, 
        'encode':output_path,
        'encodee':encodee,
        'decode':decode_path
        }
    return render(request,"home.htm",context)


def encrypt(request):
    listofimages=os.listdir("./media/Encrypted/")
    count=0
    for i in listofimages:
        count+=1
    count/=3
    count=str(int(count))

    cover="./media/extra images/cover.jpg"
    hide="./media/extra images/hidding.jpg"
    output_path="./media/extra images/encrypted.jpg"
    encodee="./media/extra images/encrypted.jpg"
    decode_path="./media/extra images/decrypted.jpg"

    fileObj=request.FILES['cover']
    fs=FileSystemStorage()
    fileNamePath=fs.save("./Encrypted/"+count+"_cover.png",fileObj)
    fileNamePath=fs.url(fileNamePath)
    cover="."+fileNamePath

    fileObj=request.FILES['hide']
    fs=FileSystemStorage()
    fileNamePath=fs.save("./Encrypted/"+count+"_hide.png",fileObj)
    fileNamePath=fs.url(fileNamePath)
    hide="."+fileNamePath

    img_visible_path=cover
    img_hidden_path=hide
    output_path="./media/Encrypted/"+count+"_encoded.png"
    img_visible = Image.open(img_visible_path)
    img_hidden = Image.open(img_hidden_path)
    h,w=img_hidden.size
    img_visible=img_visible.resize((2*h+1,2*w+1))
    encoded_image = encode(img_visible,img_hidden)
    encoded_image.save(output_path)
        
    context={
        'cover':cover,
        'hide':hide, 
        'encode':output_path,
        'encodee':encodee,
        'decode':decode_path
        }
    return render(request,"home.htm",context)

def decrypt(request):
    listofimages=os.listdir("./media/Decrypted/")
    count=0
    for i in listofimages:
        count+=1
    count/=2
    count=str(int(count))
    cover="./media/extra images/cover.jpg"
    hide="./media/extra images/hidding.jpg"
    output_path="./media/extra images/encrypted.jpg"
    encodee="./media/extra images/encrypted.jpg"
    decode_path="./media/extra images/decrypted.jpg"

    fileObj=request.FILES['encodee']
    fs=FileSystemStorage()
    fileNamePath=fs.save("./Decrypted/"+count+"_encode.png",fileObj)
    fileNamePath=fs.url(fileNamePath)
    encodee="."+fileNamePath

    encode_path= encodee
    decode_path= "./media/Decrypted/"+count+"_decoded.jpg"
    decoded_image = decode(Image.open(encode_path)) 
    decoded_image.save(decode_path)
    
    context={
        'cover':cover,
        'hide':hide, 
        'encode':output_path,
        'encodee':encodee,
        'decode':decode_path
        }
    return render(request,"home.htm",context)