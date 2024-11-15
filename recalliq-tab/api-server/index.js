// index.js
require('dotenv').config();
const express = require('express');
const axios = require('axios');
const cors = require('cors');


const app = express();
const port = 3001;

app.use(cors());
// Middleware to parse JSON request bodies
app.use(express.json());

// Function to fetch token
// const fetchToken = async () => {
//     const apiUrl = `https://login.microsoftonline.com/${process.env.TENANT_ID}/oauth2/v2.0/token`;

//     const requestParams = new URLSearchParams({
//         grant_type: 'password',
//         client_id: process.env.CLIENT_ID,
//         client_secret: process.env.CLIENT_SECRET,
//         scope: 'OnlineMeetingTranscript.Read.All OnlineMeetingArtifact.Read.All OnlineMeetings.Read',
//         username: process.env.USERNAME,
//         password: process.env.PASSWORD,
//     }).toString();

//     try {
        // const response = await axios.post(apiUrl, requestParams, {
        //     headers: {
        //         'Content-Type': 'application/x-www-form-urlencoded',
        //     },
        // });

//         console.log("Fetched Token Data:", response.data);
//         return response.data; // Return the token data
//     } catch (error) {
//         console.error("Error fetching token data:", error.response ? error.response.data : error.message);
//         throw error; // Rethrow error for handling in route
//     }
// };

const fetchAccessToken = async (tenantID, clientToken) => {
  console.log("fetchAccessToken called")
    const url = "https://login.microsoftonline.com/" + tenantID + "/oauth2/v2.0/token";
    const params = {
        client_id: process.env.CLIENT_ID,
        client_secret:process.env.CLIENT_SECRET,
        grant_type: process.env.GRANT_TYPE,
        assertion: clientToken,
        requested_token_use: process.env.REQUESTED_TOKEN_USE,
        scope: process.env.SCOPE
    };
    
    

    const accessTokenQueryParams = new URLSearchParams(params).toString();
    console.log(url)
    console.log(accessTokenQueryParams)
    const oboResponse = await axios.post(url, accessTokenQueryParams, {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
    });
    // const oboResponse = await fetch(url, {
    //     method: "POST",
    //     body: accessTokenQueryParams,
    //     headers: {
    //         Accept: "application/json",
    //         "Content-Type": "application/x-www-form-urlencoded"
    //     }
    // });
    const oboData = await oboResponse.data;
    console.log(oboData)
    if (oboResponse.status !== 200) {
        // We got an error on the OBO request. Check if it is consent required.
        if (oboData.error.toLowerCase() === 'invalid_grant' ||
            oboData.error.toLowerCase() === 'interaction_required') {
            throw('interaction_required');
        } else {
            console.log(`Error returned in OBO: ${JSON.stringify(oboData)}`);
            throw (`Error in OBO exchange ${oboResponse.status}: ${oboResponse.statusText}`);
        }
    }

    return oboData;
};

// API route to get token
app.post('/api/token', async (req, res) => {

  const tenantID = req.body.tenantId;
  const clientToken = req.body.clientSideToken;

  if (!clientToken) {
    res.status(500).send("No Id Token");
    return
  }

  try {
    const serverSideToken = await fetchAccessToken(tenantID, clientToken);
    res.send(serverSideToken);
  }
  catch (error) {
    if (error === 'interaction_required') {
      // If here, Azure AD wants to interact with the user directly, so tell the
      // client side to display a pop-up auth box
      console.log('Interaction required');
      res.status(401).json({ status: 401, statusText: INTERACTION_REQUIRED_STATUS_TEXT });
    } else {
      console.log(`Error in /fetching graph api access token: ${error}`);
      res.status(500).json({ status: 500, statusText: error })
    }
  }
});

console.log('Starting server...');
// Start the server
app.listen(port, () => {
    console.log(`Server is running at http://localhost:${port}`);
});
