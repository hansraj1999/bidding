from typing import List
from backend.handler import constants
import asyncio
from fastapi import APIRouter
import copy


MESSAGE = """\
Subject: New Order Available for Bidding, Act Fast!
Dear {recipient},

A new order is now available for bidding on FulfilNet!
Don't miss this opportunity to expand your business and secure more deliveries.

Order Details:
Article Name: {article_name}
Article Brand: {article_brand}
Article Size: {article_size}
Lowest Bid Value: {bid_value}
From Company: {company_name}
Delivery Address: {display_address}

📌 Act Fast! Submit your bid before the deadline to be considered for this order.

If you have any questions, feel free to contact our support team.
Best regards,
The FulfilNet Team
📧 hansrajdeghun@gofynd.com."""

mail_router = APIRouter()

@mail_router.post("/send/email")
async def send_email(mail_id: str, message):
    """Send email to a recipient"""
    message_bytes = message.encode("utf-8")  # ✅ Fix UnicodeEncodeError
    await constants.smtp_client.sendmail(constants.sender_email, mail_id, message_bytes)
    return {"message": "Email sent successfully!"}


async def send_email_async(mail_id, name, bid_details):
    """Send email asynchronously"""
    message = copy.deepcopy(MESSAGE)
    message = message.format(
        recipient=name,
        article_name=bid_details["item_details"]["name"],
        article_brand=bid_details["item_details"]["brand"],
        article_size=bid_details["item_details"]["size"],
        bid_value=bid_details["initial_bid_price"],
        company_name=bid_details["company_name"],
        display_address=bid_details["delivery_details"]["display_address"]
    )
    message_bytes = message.encode("utf-8")  # ✅ Fix UnicodeEncodeError
    import aiosmtplib
    import ssl
    import certifi

    constants.smtp_client = aiosmtplib.SMTP(hostname=constants.smtp_server, port=constants.port, tls_context=ssl.create_default_context(cafile=certifi.where())) #NOSONAR
    await constants.smtp_client.connect()
    await constants.smtp_client.login(constants.sender_email, constants.password)
    await constants.smtp_client.sendmail(constants.sender_email, mail_id, message_bytes)
    print(f"✅ Email sent to {mail_id}")
    await constants.smtp_client.quit()


async def send_bulk_emails(recipients, bid_details):
    """Send emails in parallel asynchronously"""
    tasks = [send_email_async(recipient[0], recipient[1], bid_details) for recipient in recipients]
    await asyncio.gather(*tasks)
