let cropper;
let currentIndex = null;
let activeComponent = null;

const cropModal = document.getElementById("cropModal");
const cropImage = document.getElementById("cropImage");

document
.querySelectorAll(".image-upload-component")
.forEach(component => {

    const imageInput =
        component.querySelector(".image-input");

    const previewContainer =
        component.querySelector(".preview-container");

    const hiddenInput =
        component.querySelector(".cropped-images-input");

    let croppedImages = [];

    imageInput.addEventListener("change", function(e){

        previewContainer.innerHTML = "";
        croppedImages = [];

        Array.from(e.target.files).forEach((file,index)=>{

            const reader = new FileReader();

            reader.onload = function(event){

                croppedImages.push(event.target.result);

                const div = document.createElement("div");

                div.classList.add("preview-item");

                div.innerHTML =
                    `<img src="${event.target.result}">`;

                div.addEventListener("click",()=>{

                    currentIndex = index;

                    activeComponent = {
                        previewContainer,
                        hiddenInput,
                        croppedImages
                    };

                    cropImage.src =
                        croppedImages[index];

                    cropModal.style.display = "block";

                    if(cropper){
                        cropper.destroy();
                    }

                    cropper = new Cropper(
                        cropImage,
                        {
                            aspectRatio: 1,
                            viewMode: 1
                        }
                    );

                });

                previewContainer.appendChild(div);

            };

            reader.readAsDataURL(file);

        });

    });

});

document
.getElementById("saveCrop")
.addEventListener("click",()=>{

    if(!cropper || !activeComponent){
        return;
    }

    const canvas = cropper.getCroppedCanvas({
        width: 800,
        height: 800
    });

    const croppedData =
        canvas.toDataURL("image/jpeg");

    activeComponent.croppedImages[currentIndex] =
        croppedData;

    activeComponent.previewContainer
        .children[currentIndex]
        .querySelector("img")
        .src = croppedData;

    activeComponent.hiddenInput.value =
        JSON.stringify(
            activeComponent.croppedImages
        );

    cropModal.style.display = "none";

    cropper.destroy();
    cropper = null;

});

document
.getElementById("cancelCrop")
.addEventListener("click",()=>{

    cropModal.style.display = "none";

    if(cropper){
        cropper.destroy();
        cropper = null;
    }

});