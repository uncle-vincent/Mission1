from celery import Celery
from celery.task import Task
import boto3

app = Celery('task_1', broker='redis://localhost:6379', backend='redis://localhost:6379')

@app.task
def add(x,y):
	return x+y

class BaseTask(app.Task):
	def on_failure(self, exc, task_id, args, kwargs, einfo):
		print('{0!r} failed: {1!r}'.format(task_id, exc))
	pass


@app.task(base=BaseTask)
def scan_ec2_instances(stack_id):
	# Any clients created from this session will use credentials

	filters = [{'Name':'instance-state-name', 'Values': ['running']},{'Name': 'tag:Stack', 'Values':[stack_id]}]
	session = boto3.session.Session()
	ec2 = session.resource('ec2')
	instances = ec2.instances.filter(Filters=filters)

	return [instance.instance_id for instance in instances]

@app.task(base=BaseTask)
def scan_ec2_elastic_ip(instance_id):
	filters = [{'Name':'instance-id', 'Values':[instance_id]}]
	session = boto3.session.Session()
	ec2 = session.resource('ec2')
	instances = ec2.instances.filter(Filters=filters)
	elastic_ips = [instance.public_ip_address for instance in instances]
	
	return elastic_ips

@app.task(base=BaseTask)
def scan_esb_volumes(stack_id):

	filters = [{'Name':'status', 'Values': ['in-use']},{'Name': 'tag:stack_id', 'Values':[stack_id]}]
	session = boto3.session.Session()
	ec2 = session.resource('ec2')
	volumes = ec2.volumes.filter(Filters=filters)

	return [volume.volume_id for volume in volumes]

@app.task(base=BaseTask)
def scan_load_balancer(stack_id):

	filters = 'LoadBalancerDescriptions[] | [?contains(LoadBalancerName, `{}`)==`true`]'.format(
		stack_id)
	session = boto3.session.Session()
	client = session.client('elb')
	paginator = client.get_paginator('describe_load_balancers')
	page_iterator = paginator.paginate(PaginationConfig={'PageSize':100})
	filtered_elbs = page_iterator.search(filters)

	return [elb['LoadBalancerName'] for elb in filtered_elbs]

@app.task(base=BaseTask)
def scan_auto_scaling_group(stack_id):

	filters = 'AutoScalingGroups[] | [?contains(Tags[?Key==`{}`].Value, `{}`)==`true`]'.format(
			'Stack', stack_id)
	session = boto3.session.Session()
	client = session.client('autoscaling')
	paginator = client.get_paginator('describe_auto_scaling_groups')
	page_iterator = paginator.paginate(PaginationConfig={'PageSize':100})
	filtered_asgs = page_iterator.search(filters)

	return [asg['AutoScalingGroupName'] for asg in filtered_asgs]

@app.task(base=BaseTask)
def scan_security_group(stack_id):
	filters = [{'Name': 'group-name', 'Values': [stack_id]}]
	session = boto3.session.Session()
	ec2 = session.resource('ec2')
	security_groups = ec2.security_groups.filter(Filters=filters)

	return [security_group.group_id for security_group in security_groups]



@app.task(base=BaseTask)
def scan_network_interface(stack_id):
	filters = [{'Name': 'group-name', 'Values': [stack_id]}]
	session = boto3.session.Session()
	ec2 = session.resource('ec2')
	network_interfaces = ec2.network_interfaces.filter(Filters=filters)

	return [network_interface.network_interface_id for network_interface in network_interfaces]

class Scan_Stack(Task):
	
	def __init__(self):
		self.session = boto3.session.Session()
		self._stack_id = None
		self.id = id

	@property
	def stack_id(self):
		return self._stack_id

	@stack_id.setter
	def set_stack_id(self, value):
		self._stack_id = value
	
	def run(self):
		self.ids = self.scan_ec2_instances()
		print self.ids
		return self.ids

	def scan_ec2_instances(self):
		# Any clients created from this session will use credentials

		self.filters = [{'Name':'instance-state-name', 'Values': ['running']},{'Name': 'tag:Stack', 'Values':[self.stack_id]}]
		ec2 = self.session.resource('ec2')
		instances = ec2.instances.filter(Filters=self.filters)

		return [instance.instance_id for instance in instances]

	def scan_security_group(self):
		pass

