"""Utility module for submitting questions to AWS S3."""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional

import boto3
import streamlit as st


def submit_question_to_s3(question_data: dict) -> bool:
    """
    Submit question to S3 bucket.
    
    Args:
        question_data: Dictionary containing question data with keys:
            - name: Submitter's name
            - email: Submitter's email
            - question: Question text
            - timestamp: ISO format timestamp
            - status: Question status (defaults to 'unanswered')
    
    Returns:
        bool: True if submission successful, False otherwise
    """
    try:
        # Get AWS credentials from Streamlit secrets
        s3_client = boto3.client(
            's3',
            aws_access_key_id=st.secrets["aws"]["access_key_id"],
            aws_secret_access_key=st.secrets["aws"]["secret_access_key"],
            region_name=st.secrets["aws"]["region"]
        )
        
        # Generate unique filename with timestamp and UUID
        filename = f"questions/{datetime.now().isoformat()}-{uuid.uuid4()}.json"
        
        # Ensure status field exists (default to 'unanswered' if not present)
        question_data_with_status = {
            **question_data,
            "status": question_data.get("status", "unanswered")
        }
        
        # Upload to S3
        s3_client.put_object(
            Bucket=st.secrets["question_submission"]["s3_bucket"],
            Key=filename,
            Body=json.dumps(question_data_with_status, indent=2),
            ContentType='application/json'
        )
        
        # Clear cache so management module sees new question immediately
        fetch_all_questions.clear()
        
        return True
    except KeyError as e:
        st.error(f":material/error: Missing configuration: {str(e)}. Please check your Streamlit secrets.")
        return False
    except Exception as e:
        st.error(f":material/error: Error submitting question to S3: {str(e)}")
        return False


def get_s3_client():
    """
    Get configured S3 client.
    
    Returns:
        boto3.client: Configured S3 client
    """
    return boto3.client(
        's3',
        aws_access_key_id=st.secrets["aws"]["access_key_id"],
        aws_secret_access_key=st.secrets["aws"]["secret_access_key"],
        region_name=st.secrets["aws"]["region"]
    )


@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes (admin-facing, less frequent updates)
def fetch_all_questions() -> List[Dict]:
    """
    Fetch all questions from S3 bucket.
    
    Returns:
        List[Dict]: List of question dictionaries, each containing:
            - name: Submitter's name
            - email: Submitter's email
            - question: Question text
            - timestamp: ISO format timestamp
            - status: Question status
            - s3_key: S3 object key (for updating)
    """
    try:
        s3_client = get_s3_client()
        bucket_name = st.secrets["question_submission"]["s3_bucket"]
        
        # List all objects in the questions/ prefix
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix="questions/"
        )
        
        questions = []
        
        if "Contents" not in response:
            return questions
        
        # Fetch and parse each question file
        for obj in response["Contents"]:
            s3_key = obj["Key"]
            
            # Skip if it's a directory
            if s3_key.endswith("/"):
                continue
            
            try:
                # Download the object
                obj_response = s3_client.get_object(
                    Bucket=bucket_name,
                    Key=s3_key
                )
                
                # Parse JSON content
                content = obj_response["Body"].read().decode("utf-8")
                question_data = json.loads(content)
                
                # Add S3 key for later updates
                question_data["s3_key"] = s3_key
                
                questions.append(question_data)
            except Exception as e:
                # Skip files that can't be parsed
                # Note: Can't use st.warning in cached function, so we'll skip silently
                continue
        
        # Sort by timestamp (newest first)
        questions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return questions
    except KeyError as e:
        # Can't use st.error in cached function, return empty list
        return []
    except Exception as e:
        # Can't use st.error in cached function, return empty list
        return []


def update_question_status(s3_key: str, new_status: str) -> bool:
    """
    Update the status of a question in S3.
    
    Args:
        s3_key: S3 object key of the question to update
        new_status: New status value (e.g., 'answered', 'in_progress', 'unanswered')
    
    Returns:
        bool: True if update successful, False otherwise
    """
    return update_question_fields(s3_key, status=new_status)


def update_question_fields(s3_key: str, status: Optional[str] = None, response: Optional[str] = None) -> bool:
    """
    Update fields of a question in S3 (status and/or response).
    
    Args:
        s3_key: S3 object key of the question to update
        status: New status value (e.g., 'answered', 'in_progress', 'unanswered')
        response: Response text to add to the question
    
    Returns:
        bool: True if update successful, False otherwise
    """
    try:
        s3_client = get_s3_client()
        bucket_name = st.secrets["question_submission"]["s3_bucket"]
        
        # Fetch the existing question
        obj_response = s3_client.get_object(
            Bucket=bucket_name,
            Key=s3_key
        )
        
        # Parse existing data
        content = obj_response["Body"].read().decode("utf-8")
        question_data = json.loads(content)
        
        # Update status if provided
        if status is not None:
            question_data["status"] = status
        
        # Update response if provided
        if response is not None:
            question_data["response"] = response
            # Add response timestamp if not already present
            if "response_timestamp" not in question_data:
                question_data["response_timestamp"] = datetime.now().isoformat()
        
        # Re-upload with updated data
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=json.dumps(question_data, indent=2),
            ContentType='application/json'
        )
        
        # Clear cache so changes are immediately visible
        fetch_all_questions.clear()
        
        return True
    except KeyError as e:
        st.error(f":material/error: Missing configuration: {str(e)}. Please check your Streamlit secrets.")
        return False
    except Exception as e:
        st.error(f":material/error: Error updating question: {str(e)}")
        return False


def delete_question(s3_key: str) -> bool:
    """
    Delete a question from S3 bucket.
    
    Args:
        s3_key: S3 object key of the question to delete
    
    Returns:
        bool: True if deletion successful, False otherwise
    """
    try:
        s3_client = get_s3_client()
        bucket_name = st.secrets["question_submission"]["s3_bucket"]
        
        # Delete the object from S3
        s3_client.delete_object(
            Bucket=bucket_name,
            Key=s3_key
        )
        
        # Clear cache so deletion is immediately visible
        fetch_all_questions.clear()
        
        return True
    except KeyError as e:
        st.error(f":material/error: Missing configuration: {str(e)}. Please check your Streamlit secrets.")
        return False
    except Exception as e:
        st.error(f":material/error: Error deleting question: {str(e)}")
        return False
