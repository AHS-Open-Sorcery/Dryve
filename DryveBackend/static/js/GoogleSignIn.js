function onSignIn(googleUser) {
    let profile = googleUser.getBasicProfile();
    console.log('ID: ' + profile.getId()); // Do not send to your backend! Use an ID token instead.
    console.log('Name: ' + profile.getName());
    console.log('Image URL: ' + profile.getImageUrl());
    console.log('Email: ' + profile.getEmail()); // This is null if the 'email' scope is not present.
    $('#token').val(googleUser.getAuthResponse().id_token);
    document.forms[0].submit();
}

function signOut() {
    let auth2 = gapi.auth2.getAuthInstance();
    auth2.signOut().then(() => {
        window.location.href = "/";
    });
}

function onLoad() {
    gapi.load('auth2', async function () {
        await gapi.auth2.init();
        signOut();
    });
}