from agentmesh.mal.adapters.base import MessagePlatformAdapter
from agentmesh.mal.message import UniversalMessage
import boto3


class SNSSQSAdapter(MessagePlatformAdapter):
    def __init__(self, region_name: str):
        self.sns = boto3.client("sns", region_name=region_name)
        self.sqs = boto3.client("sqs", region_name=region_name)

    async def send(self, message: UniversalMessage, target: str):
        if "arn:aws:sns" in target:
            self.sns.publish(TopicArn=target, Message=message.serialize().decode())
        else:
            self.sqs.send_message(
                QueueUrl=target, MessageBody=message.serialize().decode()
            )

    async def consume(self, subscription: str):
        while True:
            response = self.sqs.receive_message(
                QueueUrl=subscription, MaxNumberOfMessages=10, WaitTimeSeconds=20
            )
            if "Messages" in response:
                for msg in response["Messages"]:
                    yield UniversalMessage.deserialize(msg["Body"].encode())
                    self.sqs.delete_message(
                        QueueUrl=subscription, ReceiptHandle=msg["ReceiptHandle"]
                    )
