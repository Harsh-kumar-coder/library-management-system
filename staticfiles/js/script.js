// Auto Hide Toast Messages

setTimeout(() => {

    let alerts = document.querySelectorAll('.popup-alert');

    alerts.forEach(alert => {

        alert.classList.remove('show');

    });

}, 3000);


// Toggle Password

function togglePass(id){

    let input = document.getElementById(id);

    if(input.type === "password"){

        input.type = "text";

    }

    else{

        input.type = "password";

    }

}


// Toggle Admin Code

function toggleAdminCode(){

    let role = document.getElementById('role').value;

    let adminBox = document.getElementById('adminCodeBox');

    if(role === "admin"){

        adminBox.style.display = "flex";

    }

    else{

        adminBox.style.display = "none";

    }

}


// Professional Logout Confirm

function showLogoutConfirm(){

    let confirmLogout = confirm(
        "Do you really want to logout?"
    );

    if(confirmLogout){

        document.getElementById('logoutForm').submit();

    }

}