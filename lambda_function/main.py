import boto3
import jinja2
import json
import datetime
import os
import time

cfn = boto3.client("cloudformation")

def launch_stack(stack_name, launch_params):
    cfn = boto3.client("cloudformation")
    capabilities = ["CAPABILITY_NAMED_IAM"]
    stackdata = "Empty"
    try:
        print(f"Creating stack: {stack_name}")
        stackdata = cfn.create_stack(
            StackName=stack_name,
            DisableRollback=True,
            TemplateBody=render_template(
                launch_params.get("template_filename"),
                launch_params.get("template_params"),
            ),
            Capabilities=capabilities,
        )
        stack_id = get_stack_id_by_name(stack_name)
    except Exception as e:
        print(str(e))
    return stackdata, stack_id


def delete_stack(stack_name):
    cfn = boto3.client("cloudformation")
    stack_id = get_stack_id_by_name(stack_name)
    stackdata = "Empty"
    try:
        print(f"Deleting stack: {stack_name}")
        stackdata = cfn.delete_stack(StackName=stack_name)
    except Exception as e:
        print(str(e))
    return stackdata, stack_id


def render_template(template_filename, template_params) -> str:
    # template = download_file_from_s3(bucket_name, template_filename)
    template = read_template_file(template_filename)
    rendered_template = (
        jinja2.Environment(loader=jinja2.BaseLoader())
        .from_string(template)
        .render(**template_params)
    )
    return rendered_template


# def download_file_from_s3(bucket_name, template_file_name) -> str:
#         s3 = boto3.client("s3")
#     s3_response_object = s3.get_object(Bucket=bucket_name, Key=template_file_name)
#     return s3_response_object["Body"].read().decode("utf-8")


def read_template_file(file_name):
    with open(file_name) as f:
        stack = f.read()
    return stack

def get_stack_id_by_name(stack_name):
    return cfn.describe_stacks(StackName=stack_name).get('Stacks')[0].get('StackId')

def wait_for_stack_to_finish(stack_id, time_elapsed=0):
    stack_info = cfn.describe_stacks(StackName=stack_id)
    stack_status = stack_info['Stacks'][0].get('StackStatus')
    if stack_status.endswith("IN_PROGRESS"):
        print(f"Waiting for stack to finish processing... Time elapsed: {time_elapsed}s")
        time.sleep(10)
        return wait_for_stack_to_finish(stack_id, time_elapsed+10)
    else:
        return stack_status

def process_stream(record_values):

    stream_result = "Failed"
    print(f"Record: {record_values}")
    stack_name = record_values.get("Stackname").get("S")
    print(f"Stackname: {stack_name}")
    timestamp = record_values.get("Timestamp").get("S")
    print(f"Timestamp: {timestamp}")

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ['ActionsDynamoDbTableName'])
    # getting value from db, as it's stripped of type values that mess with the data
    response = table.get_item(
        Key={"Stackname": stack_name, "Timestamp": timestamp}
    )
    print(response)
    record = response.get("Item")

    action = record.get("Action")
    print(f"Action: {action}")
    launch_params = record.get("LaunchParams")
    print(f"LaunchParams: {launch_params}")

    if action == "Create":
        stream_result, stack_id = launch_stack(
            stack_name,
            launch_params,
        )
    elif action == "Delete":
        stream_result, stack_id = delete_stack(stack_name)
    else:
        stream_result = "No action specified - aborting"
        stack_id = None

    if stack_id is not None:
        stack_status = wait_for_stack_to_finish(stack_id)

    print(stream_result)
    print(stack_status)

    db_entry = {
        "Stackname": stack_name,
        "Status": stack_status,
        "Timestamp": datetime.datetime.now().isoformat(),
    }

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["StatesDynamoDbTableName"])
    request_result = table.put_item(Item=db_entry)

    return request_result

def request_handler(event, context):
    print(f"Received event: {event}")
    request_result = "Empty"
    try:
        body = json.loads(event.get("body"))
        action = body.get("action")
        print(f"Action: {action}")
        stack_name = body.get("stack_name", "task-two-stack")
        launch_params = body.get("launch_params")
        timestamp = datetime.datetime.now().isoformat()

        db_entry = {
            "Stackname": stack_name,
            "Timestamp": timestamp,
            "Action": action,
            "LaunchParams": launch_params,
        }

        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(os.environ["ActionsDynamoDbTableName"])
        request_result = table.put_item(Item=db_entry)
    except Exception as err:
        print(str(err))
    finally:
        print(request_result)
        return request_result


def stream_handler(event, context):
    print(f"Received event: {event}")
    stack_result = "Uninitialized"

    try:
        print(type(event))
        print(type(event.get("Records")))
        # records = json.loads(event.get("Records"))
        records = event.get("Records")
        for record in records:
            print(type(record))
            print(record.keys())
            if record.get("eventName") == "INSERT":
                stack_result = process_stream(record.get("dynamodb").get("NewImage"))
    except Exception as err:
        print(str(err))
    finally:
        print(stack_result)
        return stack_result
