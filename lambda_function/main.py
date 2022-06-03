import boto3
import jinja2
import json


def launch_stack(stack_name, launch_params):
    cfn = boto3.client("cloudformation")
    capabilities = ["CAPABILITY_NAMED_IAM"]
    stackdata = "Empty"
    try:
        print(f"Stackname: {stack_name}")
        stackdata = cfn.create_stack(
            StackName=stack_name,
            DisableRollback=True,
            TemplateBody=render_template(
                launch_params.get("template_bucket_name"),
                launch_params.get("template_filename"),
                launch_params.get("template_params"),
            ),
            Capabilities=capabilities,
        )
    except Exception as e:
        print(str(e))
    return stackdata


def delete_stack(stack_name):
    cfn = boto3.client("cloudformation")
    stackdata = "Empty"
    try:
        print(f"Stackname: {stack_name}")
        stackdata = cfn.delete_stack(StackName=stack_name)
    except Exception as e:
        print(str(e))
    return stackdata


def render_template(bucket_name, template_filename, template_params) -> str:
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


def handler(event, context):
    print(f"Received event: {event}")
    stack_result = "Uninitialized"
    try:
        body = json.loads(event.get("body"))
        action = body.get("action")
        print(f"Action: {action}")
        stack_name = body.get("stack_name", "task-one-stack")
        launch_params = body.get("launch_params")

        if action == "Create":
            stack_result = launch_stack(
                stack_name,
                launch_params,
            )

        elif action == "Delete":
            print(f"Deleting stack: {stack_name}")
            stack_result = delete_stack(stack_name)

        else:
            stack_result = "No action specified - aborting"
    except Exception as err:
        print(str(err))
    finally:
        print(stack_result)
        return stack_result
