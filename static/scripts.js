
// Login status
document.addEventListener("DOMContentLoaded", function () {
    const addFilmButton = document.getElementById("addFilmButton");
    const modifyFilmButton = document.getElementById("modifyFilmButton");

    // Check if user is logged in
    if (!isLoggedIn()) {
        // If not logged in, disable the buttons
        addFilmButton.disabled = true;
        modifyFilmButton.disabled = true;
    }
});

function isLoggedIn() {
    // Check if the session email exists (assuming session is maintained on the server)
    return "{{ session['email'] }}" !== "";
}

// Log out

// Get the modal and the cancel button
var modal = document.getElementById('logoutModal');
var cancelBtn = document.getElementById('cancelLogout');
var logoutLink = document.getElementById('logoutLink');

// Add event listener to cancel button to hide the modal
cancelBtn.addEventListener('click', function () {
    modal.style.display = 'none';
});

// Add event listener to logout link to hide the modal
logoutLink.addEventListener('click', function () {
    modal.style.display = 'none';
});


// CRUD scripts


// Field toggle views
let activeFields = null;

function toggleEdit(filmId) {
    let inputField = document.getElementById(filmId + "_mod_title");
    let inputField2 = document.getElementById(filmId + "_mod_genre");
    let inputField3 = document.getElementById(filmId + "_mod_yearReleased");
    let inputField4 = document.getElementById(filmId + "_mod_rating");
    let inputField5 = document.getElementById(filmId + "_mod_duration");
    let inputField6 = document.getElementById(filmId + "_mod_poster");
    let inputField7 = document.getElementById(filmId + "_mod_posterImg");
    let updateButton = document.getElementById(filmId + "_update");
    let row = document.getElementById(filmId + "_row");

    // Deactivate previously active fields and remove active class
    if (activeFields) {
        for (let field of Object.values(activeFields)) {
            field.readOnly = true;
            field.style.backgroundColor = "transparent";
            field.style.color = "white";
            field.style.border = "0";
        }
        activeFields.row.classList.remove("active");
        activeFields.update.style.display = "none";
        activeFields.poster.style.display = "none";
        activeFields.posterImg.style.display = "block";
    }

    inputFields = [inputField, inputField2, inputField3, inputField4, inputField5, inputField6];
    for (let field of inputFields) {
        field.readOnly = !field.readOnly;
        if (field.readOnly) {
            field.style.backgroundColor = "transparent";
            field.style.color = "white";
            field.style.border = "0";
        } else {
            field.style.backgroundColor = "white";
            field.style.color = "black";
            field.style.border = "1px solid red";
        }
    }

    inputField7.style.display = "block";
    inputField6.style.display = "none";
    row.classList.add("active");
    updateButton.classList.remove("active");

    activeFields = {
        title: inputField,
        genre: inputField2,
        yearReleased: inputField3,
        rating: inputField4,
        duration: inputField5,
        poster: inputField6,
        posterImg: inputField7,
        update: updateButton,
        row: row
    };
}

// Confirm Delete
// JavaScript to handle modal confirmation
function confirmDelete(filmId, filmTitle) {
    // Set the film title in the modal
    document.getElementById('deleteFilmTitle').textContent = filmTitle;
    // Show the modal
    var deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'), {
        keyboard: false
    });
    deleteModal.show();
    // Add event listener to the confirm delete button
    document.getElementById('confirmDeleteButton').addEventListener('click', function () {
        // Submit the form
        let form = document.getElementById(`deleteForm_${filmId}`);
        if (form) {
            // Set the value of deleteType input based on confirmation
            form.querySelector('input[name="deleteType"]').value = "single";
            // Submit the form
            form.submit();
        }
        // Close the modal
        deleteModal.hide();
    });
}




