from google import genai
from google.genai import types
from PIL import Image
import os


client = genai.Client(api_key="")

os.makedirs('results_nano_banana/cleaned_frames_nbpro', exist_ok=True)
for frame in os.listdir('results_nano_banana/frames'):
    # frame = 'frame22.png'
    print(frame)
    image = Image.open(os.path.join('results_nano_banana/frames', frame))
    low_res_image = image.resize((1248//10, 832//10))
    low_res_image = low_res_image.resize((1248, 832))
    os.makedirs('results_nano_banana/cleaned_frames_nbpro/'+frame[:-4], exist_ok=True)
    image.save(os.path.join('results_nano_banana/cleaned_frames_nbpro/'+frame[:-4], frame))
    low_res_image.save(os.path.join('results_nano_banana/cleaned_frames_nbpro/'+frame[:-4], frame[:-4]+'_low_res.png'))
    
    prompt1 = (
        f"Create a colored depth map of this image. Do not change the contour lines. Do not introduce glares. Do not alter the scene.",
    )
    prompt2 = (
        f"aspect_ratio=\"3:2\". Recover the original image in natural light with high resolution. Do not introduce glares. Do not alter the scene.",
    )
    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[prompt1, image],
    )

    for part in response.parts:
        if part.text is not None:
            print(part.text)
        elif part.inline_data is not None:
            depth_map = part.as_image()
            depth_map.save(os.path.join('results_nano_banana/cleaned_frames_nbpro/'+frame[:-4], frame[:-4]+'_depth_map.png'))
    depth_map = Image.open(os.path.join('results_nano_banana/cleaned_frames_nbpro', frame[:-4], frame[:-4]+'_depth_map.png'))

    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[prompt2, low_res_image, depth_map],
    )

    for part in response.parts:
        if part.text is not None:
            print(part.text)
        elif part.inline_data is not None:
            cleaned_image = part.as_image()
            cleaned_image.save(os.path.join('results_nano_banana/cleaned_frames_nbpro/'+frame[:-4], frame[:-4]+'_cleaned.png'))