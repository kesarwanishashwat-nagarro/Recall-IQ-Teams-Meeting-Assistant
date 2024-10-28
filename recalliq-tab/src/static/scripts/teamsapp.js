(function () {
  "use strict";

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

  // Get a client side token from Teams
  async function getClientSideToken() {
    return new Promise((resolve, reject) => {
      microsoftTeams.authentication.getAuthToken({
        successCallback: (result) => {
          console.log("Auth Token received successfully.");
          resolve(result);
        },
        failureCallback: (error) => {
          console.log("Failed to get Auth Token:", error);
          reject(error);
        }
      });
    });
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
      const clientSideToken = await getClientSideToken();
      const userProfile = await getGraphAccessToken(clientSideToken);

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
