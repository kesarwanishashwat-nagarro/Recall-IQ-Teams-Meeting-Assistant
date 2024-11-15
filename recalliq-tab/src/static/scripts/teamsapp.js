(function () {
  "use strict";
  var clientSideToken = '';
  var txtArea = document.getElementById('joinUrlTxtArea');
  var btnSubmit = document.getElementById('btn-submit');
  var loading = document.getElementById('loading');
  var subSuccess = document.getElementById('sub-success');
  var urlContent = document.getElementById('url-content');
  if(btnSubmit){
    btnSubmit.addEventListener('click', onBtnSubmit)
  }
  if(txtArea){
    txtArea.addEventListener('input', onJoinUrlChange)
  }
  // Call the initialize API first
  microsoftTeams.app.initialize().then(function () {
    microsoftTeams.app.getContext().then(function (context) {
      if (context?.app?.host?.name) {
        console.log(context.app.host.name)
      }
    });
    
    // Fetch and display the user profile using auth token
    displayUI();
  });

  function validURL(str) {
    var pattern = new RegExp('^(https?:\\/\\/)?'+ // protocol
      '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|'+ // domain name
      '((\\d{1,3}\\.){3}\\d{1,3}))'+ // OR ip (v4) address
      '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*'+ // port and path
      '(\\?[;&a-z\\d%_.~+=-]*)?'+ // query string
      '(\\#[-a-z\\d_]*)?$','i'); // fragment locator
    return !!pattern.test(str);
  }

  function onJoinUrlChange(event){
    const url = event.target.value;
    if(url){
      btnSubmit.disabled = false;
    } else {
      btnSubmit.disabled = true;
    }
  }

  async function onBtnSubmit(){
    if(clientSideToken){
      try {
        await subscribeMeetingEvents(clientSideToken)
        urlContent.style.display = 'none';
        subSuccess.style.display = 'block';
      } catch(e){
        console.error(e);
      }
    }
  }

  // Get a client side token from Teams
  async function getClientSideToken() {
    return new Promise((resolve, reject) => {
      microsoftTeams.authentication.getAuthToken({
        successCallback: (result) => {
          console.log("Auth Token received successfully.");
          console.log(result);
          loading.style.display = 'none';
          urlContent.style.display = 'block';
          resolve(result);
        },
        failureCallback: (error) => {
          console.log("Failed to get Auth Token:", error);
          reject(error);
        }
      });
    });
  }

  async function subscribeMeetingEvents(clientSideToken){
    console.log(txtArea.value)
    const context = await (() => {
      return new Promise((resolve) => {
        microsoftTeams.getContext(context => resolve(context));
      })
    })();

    // Request the user profile from our web service
    const response = await fetch('http://localhost:5000/subscribe', {
      method: 'post',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        'userId': "1ada3a13-67fa-47e0-928f-af150f8c0e29",
        'token': clientSideToken,
        'JoinWebUrl': txtArea.value
      }),
      cache: 'default'
    });

    if (response.ok) {
      return;
    } else {
      const error = await response.json();
      throw (error);
    }
  }

  // Get the user profile from our web service
  async function getGraphAccessToken(clientSideToken) {
    if (!clientSideToken) {
      throw ("Error: No client side token provided in getGraphAccessToken()");
    }

    // Get Teams context, converting callback to a promise so we can await it
    const context = await (() => {
      return new Promise((resolve) => {
        microsoftTeams.getContext(context => resolve(context));
      })
    })();

    // Request the user profile from our web service
    const response = await fetch('http://localhost:3001/api/token', {
      method: 'post',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        'tenantId': context.tid,
        'clientSideToken': clientSideToken
      }),
      cache: 'default'
    });

    if (response.ok) {
      const userProfile = await response.json();
      return userProfile;
    } else {
      const error = await response.json();
      throw (error);
    }
  }

  // Render the page on load or after a consent
  async function displayUI() {
    const displayElement = document.getElementById('content');
    try {
      clientSideToken = await getClientSideToken();
      // const userProfile = await getGraphAccessToken(clientSideToken);

      // displayElement.innerHTML = `
      //   <h1>${userProfile.access_token}</h1>
      // `;
    } catch (error) {
      if (error.statusText === 'interaction_required') {
        // If Azure AD wants to interact with the user, show consent popup
        displayElement.innerText = '';
        const button = document.createElement('button');
        button.innerText = 'Consent required';
        button.onclick = showConsentPopup;
        displayElement.appendChild(button);
      } else {
        // Other error handling
        console.log(`Error: ${JSON.stringify(error)}`)
        displayElement.innerText = "Oops! Something went wrong. Please try again later.";
        displayElement.style.color = "red";
      }
    }
  }

  // Display the consent pop-up if needed
  async function showConsentPopup() {
    await microsoftTeams.authentication.authenticate({
      url: window.location.origin + "/consent-popup-start.html",
      width: 600,
      height: 535,
      successCallback: (() => {
        console.log('Got success callback');
        displayUI();
      })
    });
  }
})();
