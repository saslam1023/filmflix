
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
        activeFields.title.readOnly = true;
        activeFields.genre.readOnly = true;
        activeFields.rating.readOnly = true;
        activeFields.yearReleased.readOnly = true;
        activeFields.duration.readOnly = true;
        activeFields.poster.readOnly = true;
        activeFields.row.classList.remove("active");
        activeFields.update.style.display = ("none");
        activeFields.poster.style.display = ("none");


        // Revert styling changes for previously active fields
        activeFields.title.style.backgroundColor = "transparent";
        activeFields.title.style.color = "white";
        activeFields.title.style.border = "0";
        activeFields.genre.style.backgroundColor = "transparent";
        activeFields.genre.style.color = "white";
        activeFields.genre.style.border = "0";
        activeFields.rating.style.backgroundColor = "transparent";
        activeFields.rating.style.color = "white";
        activeFields.rating.style.border = "0";
        activeFields.duration.style.backgroundColor = "transparent";
        activeFields.duration.style.color = "white";
        activeFields.duration.style.border = "0";
        activeFields.yearReleased.style.backgroundColor = "transparent";
        activeFields.yearReleased.style.color = "white";
        activeFields.yearReleased.style.border = "0";
        activeFields.poster.style.backgroundColor = "transparent";
        activeFields.poster.style.color = "white";
        activeFields.poster.style.border = "0";
        activeFields.posterImg.style.display = "block";

    }

    // Activate fields in the clicked row
    inputField.readOnly = !inputField.readOnly;
    inputField2.readOnly = !inputField2.readOnly;
    inputField3.readOnly = !inputField3.readOnly;
    inputField4.readOnly = !inputField4.readOnly;
    inputField5.readOnly = !inputField5.readOnly;
    inputField6.readOnly = !inputField6.readOnly;
    inputField7.style.display = "block";
    inputField6.style.display = "none";
    row.classList.add("active");
    updateButton.classList.remove("active");



    // Apply styling changes based on read-only status
    if (inputField.readOnly) {
        inputField.style.backgroundColor = "transparent";
        inputField.style.color = "white";
        inputField.style.border = "0";
        updateButton.style.display = "none";
        inputField7.style.display = "block";
        inputField6.style.display = "none";
        inputField2.style.backgroundColor = "transparent";
        inputField2.style.color = "white";
        inputField2.style.border = "0";
        inputField3.style.backgroundColor = "transparent";
        inputField3.style.color = "white";
        inputField3.style.border = "0";
        inputField4.style.backgroundColor = "transparent";
        inputField4.style.color = "white";
        inputField4.style.border = "0";
        inputField5.style.backgroundColor = "transparent";
        inputField5.style.color = "white";
        inputField5.style.border = "0";
        inputField6.style.backgroundColor = "transparent";
        inputField6.style.color = "white";
        inputField6.style.border = "0";
    } else {
        inputField.style.backgroundColor = "white";
        inputField.style.color = "black";
        inputField.style.border = "1px solid red";
        inputField2.style.backgroundColor = "white";
        inputField2.style.color = "black";
        inputField2.style.border = "1px solid red";
        inputField3.style.backgroundColor = "white";
        inputField3.style.color = "black";
        inputField3.style.border = "1px solid red";
        inputField4.style.backgroundColor = "white";
        inputField4.style.color = "black";
        inputField4.style.border = "1px solid red";
        inputField5.style.backgroundColor = "white";
        inputField5.style.color = "black";
        inputField5.style.border = "1px solid red";
        inputField6.style.backgroundColor = "white";
        inputField6.style.color = "black";
        inputField6.style.border = "1px solid red";
        updateButton.style.display = "block";
        inputField7.style.display = "none";
        inputField6.style.display = "block";


    }

    // Update active fields
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




