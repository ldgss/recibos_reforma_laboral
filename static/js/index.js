const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const mensaje_sin_archivo = document.getElementById('mensaje_sin_archivo');
const mensaje_con_archivo = document.getElementById('mensaje_con_archivo');
const nombreArchivo = document.getElementById('nombreArchivo');
const submit_button = document.getElementById('submit_button');
const uploadForm = document.getElementById("uploadForm");
const loadingOverlay = document.getElementById("loadingOverlay");

uploadForm.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!fileInput.files.length) {
        dropzone.classList.remove("parpadeo");
        void dropzone.offsetWidth;
        dropzone.classList.add("parpadeo");
        setTimeout(() => {
            dropzone.classList.remove("parpadeo");
        }, 600);
        return;
    }
    loadingOverlay.style.display = "block";
    uploadForm.submit();
});

dropzone.addEventListener('click', () => fileInput.click());

dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
});

dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
});

dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        mostrarArchivo(fileInput.files[0]);
    }
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length) {
        mostrarArchivo(fileInput.files[0]);
    }
});

function mostrarArchivo(file) {
    dropzone.classList.add('has-file');
    mensaje_sin_archivo.style.display = "none"
    mensaje_con_archivo.style.display = "block"
    nombreArchivo.textContent = file.name;
}

function ocultarOverlay() {
    loadingOverlay.style.display = "none";
    mensaje_sin_archivo.style.display = "block"
    mensaje_con_archivo.style.display = "none"
    nombreArchivo.textContent = ""
    uploadForm.reset()
}

window.addEventListener("pageshow", ocultarOverlay);