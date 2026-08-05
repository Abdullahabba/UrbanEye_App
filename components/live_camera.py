from PIL import Image
import numpy as np
import cv2

# Check if processed image exists in session state
if "processed_img" in st.session_state and st.session_state["processed_img"] is not None:
    img = st.session_state["processed_img"]
    
    # Agar numpy array hai (YOLO/OpenCV output), to usay RGB aur PIL Image mein convert karein
    if isinstance(img, np.ndarray):
        # Agar image BGR format mein hai to RGB karein (YOLO .plot() default BGR deta hai)
        if len(img.shape) == 3 and img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        
    st.image(img, caption="Live Camera AI Result", use_container_width=True)
