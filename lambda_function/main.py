import boto3
import jinja2


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
    template = download_file_from_s3(bucket_name, template_filename)
    rendered_template = (
        jinja2.Environment(loader=jinja2.BaseLoader())
        .from_string(template)
        .render(**template_params)
    )
    return rendered_template


def download_file_from_s3(bucket_name, template_file_name) -> str:
    s3 = boto3.client("s3")
    s3_response_object = s3.get_object(Bucket=bucket_name, Key=template_file_name)
    return s3_response_object["Body"].read().decode("utf-8")


def handler(event, context):
    print(f"Received event: {event}")
    action = event.get("action")
    stack_name = event.get("stack_name", "task-one-stack")
    launch_params = event.get("launch_params")
    if action == "Create":
        stack_result = launch_stack(
            stack_name,
            launch_params,
        )
    elif action == "Delete":
        print(f"Deleting stack: {stack_name}")
        stack_result = delete_stack(
            stack_name
        )
    else:
        stack_result = "No action specified - aborting"

    print(stack_result)
    return stack_result