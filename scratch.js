const xhr = new XMLHttpRequest();
try {
    xhr.send(formData);
} catch (e) {
    console.log("Error caught:", e.message);
}
