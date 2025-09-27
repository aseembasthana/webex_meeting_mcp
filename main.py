"""
Webex MCP Server - A Model Context Protocol server for Cisco Webex using FastMCP
Provides standardized AI model access to Webex meetings and messaging APIs via HTTP streaming
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webex-mcp")

class WebexAPI:
    """Webex API client for making authenticated requests"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://webexapis.com/v1"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None, 
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make authenticated HTTP request to Webex API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=self.headers, params=params)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=self.headers, json=data)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=self.headers, json=data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=self.headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json() if response.content else {}
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error: {e}")
                raise Exception(f"API request failed: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise Exception(f"Request failed: {str(e)}")

# Initialize FastMCP
mcp = FastMCP("Webex MCP Server")

# Global Webex API instance
webex_api = None

def get_webex_api() -> WebexAPI:
    """Get or create Webex API instance"""
    global webex_api
    if webex_api is None:
        access_token = os.getenv("WEBEX_ACCESS_TOKEN")
        if not access_token:
            raise ValueError("WEBEX_ACCESS_TOKEN environment variable is required")
        webex_api = WebexAPI(access_token)
    return webex_api

# ========== MEETINGS TOOLS ==========

@mcp.tool()
async def list_meetings(
    meetingType: Optional[str] = None,
    state: Optional[str] = None,
    scheduledType: Optional[str] = None,
    current: Optional[bool] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    max: Optional[int] = None
) -> str:
    """
    List meetings for the authenticated user.
    
    Args:
        meetingType: Type of meeting (meeting, webinar, personalRoomMeeting)
        state: Meeting state (active, scheduled, ended, inProgress)
        scheduledType: Scheduled type (meeting, webinar)
        current: List only current user's meetings
        from_date: Start date (ISO 8601 format)
        to_date: End date (ISO 8601 format)
        max: Maximum number of meetings to return (1-100)
    """
    webex = get_webex_api()
    params = {}
    
    if meetingType:
        params["meetingType"] = meetingType
    if state:
        params["state"] = state
    if scheduledType:
        params["scheduledType"] = scheduledType
    if current is not None:
        params["current"] = current
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    if max:
        params["max"] = max
    
    result = await webex._make_request("GET", "/meetings", params=params)
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_meeting_details(meeting_id: str, current: Optional[bool] = None) -> str:
    """
    Get detailed information about a specific meeting.
    
    Args:
        meeting_id: The meeting ID
        current: Whether to show only current user info
    """
    webex = get_webex_api()
    params = {}
    if current is not None:
        params["current"] = current
    
    result = await webex._make_request("GET", f"/meetings/{meeting_id}", params=params)
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_meeting_transcript(meeting_id: str, format: Optional[str] = None) -> str:
    """
    Get transcript for a meeting.
    
    Args:
        meeting_id: The meeting ID
        format: Transcript format (txt, vtt, srt)
    """
    webex = get_webex_api()
    params = {}
    if format:
        params["format"] = format
    
    try:
        # Note: Transcript endpoint may vary - adjust based on actual Webex API
        result = await webex._make_request("GET", f"/meetings/{meeting_id}/transcripts", params=params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Transcript not available: {str(e)}"

@mcp.tool()
async def get_recording(recording_id: str) -> str:
    """
    Get recording details for a meeting.
    
    Args:
        recording_id: The recording ID
    """
    webex = get_webex_api()
    result = await webex._make_request("GET", f"/recordings/{recording_id}")
    return json.dumps(result, indent=2)

@mcp.tool()
async def list_recordings(
    meeting_id: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    max: Optional[int] = None
) -> str:
    """
    List recordings.
    
    Args:
        meeting_id: Filter by meeting ID
        from_date: Start date (ISO 8601 format)
        to_date: End date (ISO 8601 format)
        max: Maximum number of recordings to return
    """
    webex = get_webex_api()
    params = {}
    
    if meeting_id:
        params["meetingId"] = meeting_id
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    if max:
        params["max"] = max
    
    result = await webex._make_request("GET", "/recordings", params=params)
    return json.dumps(result, indent=2)

@mcp.tool()
async def create_meeting(
    title: str,
    agenda: Optional[str] = None,
    password: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    timezone: Optional[str] = None,
    enabledAutoRecordMeeting: Optional[bool] = None,
    allowAnyUserToBeCoHost: Optional[bool] = None,
    invitees: Optional[str] = None
) -> str:
    """
    Create a new meeting.
    
    Args:
        title: Meeting title
        agenda: Meeting agenda
        password: Meeting password
        start: Start time (ISO 8601 format)
        end: End time (ISO 8601 format)
        timezone: Timezone
        enabledAutoRecordMeeting: Auto record meeting
        allowAnyUserToBeCoHost: Allow any user to be co-host
        invitees: JSON array of invitee objects with email and optional displayName
    """
    webex = get_webex_api()
    data = {"title": title}
    
    if agenda:
        data["agenda"] = agenda
    if password:
        data["password"] = password
    if start:
        data["start"] = start
    if end:
        data["end"] = end
    if timezone:
        data["timezone"] = timezone
    if enabledAutoRecordMeeting is not None:
        data["enabledAutoRecordMeeting"] = enabledAutoRecordMeeting
    if allowAnyUserToBeCoHost is not None:
        data["allowAnyUserToBeCoHost"] = allowAnyUserToBeCoHost
    
    if invitees:
        try:
            data["invitees"] = json.loads(invitees)
        except json.JSONDecodeError:
            return "Error: Invalid JSON format for invitees"
    
    result = await webex._make_request("POST", "/meetings", data=data)
    return json.dumps(result, indent=2)

@mcp.tool()
async def update_meeting(
    meeting_id: str,
    title: Optional[str] = None,
    agenda: Optional[str] = None,
    password: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    timezone: Optional[str] = None
) -> str:
    """
    Update an existing meeting.
    
    Args:
        meeting_id: The meeting ID
        title: Meeting title
        agenda: Meeting agenda
        password: Meeting password
        start: Start time (ISO 8601 format)
        end: End time (ISO 8601 format)
        timezone: Timezone
    """
    webex = get_webex_api()
    data = {}
    
    if title:
        data["title"] = title
    if agenda:
        data["agenda"] = agenda
    if password:
        data["password"] = password
    if start:
        data["start"] = start
    if end:
        data["end"] = end
    if timezone:
        data["timezone"] = timezone
    
    result = await webex._make_request("PUT", f"/meetings/{meeting_id}", data=data)
    return json.dumps(result, indent=2)

@mcp.tool()
async def delete_meeting(meeting_id: str, sendEmail: Optional[bool] = None) -> str:
    """
    Delete a meeting.
    
    Args:
        meeting_id: The meeting ID
        sendEmail: Send email notification
    """
    webex = get_webex_api()
    params = {}
    if sendEmail is not None:
        params["sendEmail"] = sendEmail
    
    await webex._make_request("DELETE", f"/meetings/{meeting_id}", params=params)
    return f"Meeting {meeting_id} deleted successfully"

@mcp.tool()
async def add_participants(meeting_id: str, participants: str) -> str:
    """
    Add participants to a meeting.
    
    Args:
        meeting_id: The meeting ID
        participants: JSON array of participant objects with email and optional role
    """
    webex = get_webex_api()
    try:
        participants_data = json.loads(participants)
        data = {"invitees": participants_data}
        result = await webex._make_request("POST", f"/meetings/{meeting_id}/invitees", data=data)
        return json.dumps(result, indent=2)
    except json.JSONDecodeError:
        return "Error: Invalid JSON format for participants"

@mcp.tool()
async def remove_participants(meeting_id: str, participant_ids: str) -> str:
    """
    Remove participants from a meeting.
    
    Args:
        meeting_id: The meeting ID
        participant_ids: JSON array of participant IDs to remove
    """
    webex = get_webex_api()
    try:
        ids = json.loads(participant_ids)
        # Note: This endpoint structure may need adjustment based on actual API
        for participant_id in ids:
            await webex._make_request("DELETE", f"/meetings/{meeting_id}/invitees/{participant_id}")
        return "Participants removed successfully"
    except json.JSONDecodeError:
        return "Error: Invalid JSON format for participant IDs"

@mcp.tool()
async def list_participants(
    meeting_id: str,
    joinedBefore: Optional[str] = None,
    joinedAfter: Optional[str] = None,
    max: Optional[int] = None
) -> str:
    """
    List participants of a meeting.
    
    Args:
        meeting_id: The meeting ID
        joinedBefore: Filter participants who joined before this time
        joinedAfter: Filter participants who joined after this time
        max: Maximum number of participants to return
    """
    webex = get_webex_api()
    params = {}
    
    if joinedBefore:
        params["joinedBefore"] = joinedBefore
    if joinedAfter:
        params["joinedAfter"] = joinedAfter
    if max:
        params["max"] = max
    
    result = await webex._make_request("GET", f"/meetings/{meeting_id}/participants", params=params)
    return json.dumps(result, indent=2)

# ========== MESSAGING TOOLS ==========

@mcp.tool()
async def list_spaces(
    teamId: Optional[str] = None,
    type: Optional[str] = None,
    sortBy: Optional[str] = None,
    max: Optional[int] = None
) -> str:
    """
    List spaces (rooms) the user is a member of.
    
    Args:
        teamId: Filter by team ID
        type: Space type (direct, group)
        sortBy: Sort by (id, lastactivity, created)
        max: Maximum number of spaces to return
    """
    webex = get_webex_api()
    params = {}
    
    if teamId:
        params["teamId"] = teamId
    if type:
        params["type"] = type
    if sortBy:
        params["sortBy"] = sortBy
    if max:
        params["max"] = max
    
    result = await webex._make_request("GET", "/rooms", params=params)
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_messages(
    roomId: str,
    mentionedPeople: Optional[str] = None,
    before: Optional[str] = None,
    beforeMessage: Optional[str] = None,
    max: Optional[int] = None
) -> str:
    """
    Get messages from a space.
    
    Args:
        roomId: The space/room ID
        mentionedPeople: Filter messages that mention specific people
        before: List messages before this date
        beforeMessage: List messages before this message ID
        max: Maximum number of messages to return
    """
    webex = get_webex_api()
    params = {"roomId": roomId}
    
    if mentionedPeople:
        params["mentionedPeople"] = mentionedPeople
    if before:
        params["before"] = before
    if beforeMessage:
        params["beforeMessage"] = beforeMessage
    if max:
        params["max"] = max
    
    result = await webex._make_request("GET", "/messages", params=params)
    return json.dumps(result, indent=2)

@mcp.tool()
async def send_message(
    roomId: Optional[str] = None,
    toPersonId: Optional[str] = None,
    toPersonEmail: Optional[str] = None,
    text: Optional[str] = None,
    markdown: Optional[str] = None,
    html: Optional[str] = None,
    files: Optional[str] = None
) -> str:
    """
    Send a message to a space or person.
    
    Args:
        roomId: The space/room ID to send message to
        toPersonId: Person ID for direct message
        toPersonEmail: Person email for direct message
        text: Message text content
        markdown: Message markdown content
        html: Message HTML content
        files: JSON array of file URLs to attach
    """
    webex = get_webex_api()
    data = {}
    
    # Validate destination
    if not any([roomId, toPersonId, toPersonEmail]):
        return "Error: Must specify roomId, toPersonId, or toPersonEmail"
    
    # Validate content
    if not any([text, markdown, html]):
        return "Error: Must specify text, markdown, or html content"
    
    if roomId:
        data["roomId"] = roomId
    if toPersonId:
        data["toPersonId"] = toPersonId
    if toPersonEmail:
        data["toPersonEmail"] = toPersonEmail
    if text:
        data["text"] = text
    if markdown:
        data["markdown"] = markdown
    if html:
        data["html"] = html
    
    if files:
        try:
            data["files"] = json.loads(files)
        except json.JSONDecodeError:
            return "Error: Invalid JSON format for files"
    
    result = await webex._make_request("POST", "/messages", data=data)
    return json.dumps(result, indent=2)

@mcp.tool()
async def create_space(
    title: str,
    teamId: Optional[str] = None,
    classificationId: Optional[str] = None,
    isLocked: Optional[bool] = None,
    isPublic: Optional[bool] = None,
    description: Optional[str] = None
) -> str:
    """
    Create a new space.
    
    Args:
        title: Space title
        teamId: Team ID to create space in
        classificationId: Classification ID
        isLocked: Whether space is locked
        isPublic: Whether space is public
        description: Space description
    """
    webex = get_webex_api()
    data = {"title": title}
    
    if teamId:
        data["teamId"] = teamId
    if classificationId:
        data["classificationId"] = classificationId
    if isLocked is not None:
        data["isLocked"] = isLocked
    if isPublic is not None:
        data["isPublic"] = isPublic
    if description:
        data["description"] = description
    
    result = await webex._make_request("POST", "/rooms", data=data)
    return json.dumps(result, indent=2)

@mcp.tool()
async def add_member_to_space(
    roomId: str,
    personId: Optional[str] = None,
    personEmail: Optional[str] = None,
    isModerator: Optional[bool] = None
) -> str:
    """
    Add a member to a space.
    
    Args:
        roomId: The space/room ID
        personId: Person ID to add
        personEmail: Person email to add
        isModerator: Make person a moderator
    """
    webex = get_webex_api()
    
    if not any([personId, personEmail]):
        return "Error: Must specify personId or personEmail"
    
    data = {"roomId": roomId}
    
    if personId:
        data["personId"] = personId
    if personEmail:
        data["personEmail"] = personEmail
    if isModerator is not None:
        data["isModerator"] = isModerator
    
    result = await webex._make_request("POST", "/memberships", data=data)
    return json.dumps(result, indent=2)

# ========== SERVER SETUP ==========

if __name__ == "__main__":
    import uvicorn
    
    # Validate environment variables
    access_token = os.getenv("WEBEX_ACCESS_TOKEN")
    if not access_token:
        logger.error("WEBEX_ACCESS_TOKEN environment variable is required")
        exit(1)
    
    # Initialize global Webex API instance
    webex_api = WebexAPI(access_token)
    
    # Server configuration from environment variables
    MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
    MCP_PORT = int(os.getenv("MCP_PORT", "8080"))
    SERVER_NAME = os.getenv("SERVER_NAME", "Webex MCP Server")
    TRANSPORT = os.getenv("TRANSPORT", "streamable-http")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"Starting {SERVER_NAME}...")
    logger.info("Available tools:")
    logger.info("  Meetings: list_meetings, get_meeting_details, get_meeting_transcript, get_recording, list_recordings")
    logger.info("           create_meeting, update_meeting, delete_meeting, add_participants, remove_participants, list_participants")
    logger.info("  Messaging: list_spaces, get_messages, send_message, create_space, add_member_to_space")
    logger.info(f"\nServer starting with {TRANSPORT} transport...")
    logger.info(f"Server will be available at: http://{MCP_HOST}:{MCP_PORT}/mcp")
    
    if DEBUG:
        logger.info("Debug mode: ON")
    
    # Run with configured transport and host/port settings
    mcp.run(transport=TRANSPORT, host=MCP_HOST, port=MCP_PORT)