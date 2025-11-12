const fileInput = document.getElementById("fileInput");
const uploadBtn = document.getElementById("uploadBtn");
const previewContainer = document.getElementById("previewContainer");
const previewImage = document.getElementById("previewImage");
const imageLink = document.getElementById("imageLink");

fileInput.addEventListener("change", () => {
  if (fileInput.files.length > 0) {
    uploadBtn.disabled = false;
    const file = fileInput.files[0];
    previewImage.src = URL.createObjectURL(file);
    previewContainer.classList.remove("hidden");
  } else {
    uploadBtn.disabled = true;
  }
});

uploadBtn.addEventListener("click", async () => {
  const file = fileInput.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  try {
    uploadBtn.textContent = "Завантаження...";
    uploadBtn.disabled = true;

    const response = await fetch("http://localhost:8000/upload", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) throw new Error("Не вдалося завантажити");

    const data = await response.json();
    const link = `http://localhost:8080/images/${data.filename}`;

    imageLink.textContent = link;
    imageLink.style.display = "block";
  } catch (error) {
    alert("Помилка: " + error.message);
  } finally {
    uploadBtn.textContent = "Завантажити";
    uploadBtn.disabled = false;
  }
});
