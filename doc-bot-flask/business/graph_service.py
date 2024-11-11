import datetime
import string
import pytz
import secrets
import requests
from flask import current_app, jsonify


class GraphService:    
    access_token = None
    
    def __init__(self, access_token):
        self.__class__.access_token = access_token
    
    def get_meeting_id(self, join_web_url, user_id):
        headers = {
            "Authorization": f"Bearer {self.__class__.access_token}",
            "Content-Type": "application/json"
        }
        response = requests.get(f"{current_app.config['GRAPH_API_ENDPOINT']}/users/{user_id}/onlineMeetings/?$filter=JoinWebUrl eq '{join_web_url}'",
                                 headers=headers)
        data = response.json()
        value = data["value"]
        return value.id
        
    
    def subscribe_meeting_transcripts(self, meeting_id):
        gmt_time = datetime.datetime.now(pytz.timezone('GMT'))
        # if self.__class__.access_token:
        #     self.__class__.access_token = self.__class__.access_token  # Modify class variable
        subscription_data = {
            "changeType": "created",
            "notificationUrl": f"{current_app.config['APP_URL']}/notifications",
            "resource": "communications/onlineMeetings/" + meeting_id + "/transcripts?useResourceSpecificConsentBasedAuthorization=true&includeResourceData=true",
            "expirationDateTime": (gmt_time + datetime.timedelta(minutes=45)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            "clientState": secrets.token_hex(16)
        }
        headers = {
            "Authorization": f"Bearer {self.__class__.access_token}",
            "Content-Type": "application/json"
        }
        response = requests.post(f"{current_app.config['GRAPH_API_ENDPOINT']}/subscriptions", headers=headers, json=subscription_data)
        
        if response.status_code == 201:
            return jsonify({"message": "Subscription created successfully", "data": response.json()}), 201
        else:
            return jsonify({"error": "Failed to create subscription", "details": response.json()}), response.status_code

    def download_transcript_content(self, transcript_id, meeting_id, stored_transcripts):
            if stored_transcripts and meeting_id not in stored_transcripts:
                stored_transcripts.append(meeting_id)
                url = f"{current_app.config['GRAPH_API_ENDPOINT']}/me/onlineMeetings/{meeting_id}/transcripts/{transcript_id}/content"
                headers = {
                    "Authorization": f"Bearer {self.__class__.access_token}"
                }
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    transcript_content = response.json()
                    
                    return transcript_content
                else:
                    raise Exception(f"Failed to download transcript: {response.status_code}")
        
