"""AWS Lambda functions for EBS Volume Snapshots"""

import boto3
from datetime import tzinfo, timedelta, datetime

DAYS_TO_KEEP = 30

class UTC(tzinfo):
    """
    A `tzinfo' derived class for representing UTC.

    Necessary for getting an offset-aware `datetime' object to represent "now"
    in order to calculate date deltas.

    There may be classes that make it more convenient to determine these
    deltas, but I am trying not to include dependencies unless I have to.
    """
    def __init__(self, *args, **kwargs):
        self.__zero_delta = timedelta(0)
        super(UTC, self).__init__(*args, **kwargs)
    def utcoffset(self, dt):
        return self.__zero_delta
    def tzname(self, dt):
        return 'UTC'
    def dst(self, dt):
        return self.__zero_delta

def make_snapshots(event, context):
    """Make EBS snapshots from all volumes tagged with "Backup" == "true" """
    client = boto3.client('ec2')
    vols = client.describe_volumes()['Volumes']
    vols_to_do = (v for v in vols if has_backup_tag(v))
    for v in vols_to_do:
        s = client.create_snapshot(
            VolumeId=v['VolumeId'],
            Description=volume_desc(v))
        name = snapshot_name(v)
        client.create_tags(
            Resources=[s['SnapshotId']],
            Tags=[{'Key': 'Name', 'Value': name}])

def delete_old_snapshots(event, context):
    """Delete old snapshots older than DAYS_TO_KEEP days

    It may be worthwhile to have the days parameter optionally come from
    a JSON Constant, declared in the "inputs" section of a Rule in a CloudWatch
    scheduled event.
    """
    account = event['account']
    client = boto3.client('ec2')
    snaps = client.describe_snapshots(OwnerIds=[account])['Snapshots']
    old_snaps = (s for s in snaps if older_than(s['StartTime'], DAYS_TO_KEEP))
    for s in old_snaps:
        client.delete_snapshot(SnapshotId=s['SnapshotId'])

def older_than(startdate, days):
    nowdate = datetime.now(UTC())
    return (nowdate - startdate).days > days

def has_backup_tag(volume):
    tags = volume.get('Tags', [])
    for t in tags:
        if t['Key'] == 'Backup' and t['Value'] == 'true':
            return True
    return False

def volume_desc(volume):
    tags = volume.get('Tags', [])
    name = name_tag(tags)
    if name:
        return "Backup of %s" % name
    else:
        return "Backup of %s" % volume['VolumeId']

def name_tag(tags):
    if tags:
        for t in tags:
            if t['Key'] == 'Name':
                return t['Value']
    return ''

def snapshot_name(volume):
    name = name_tag(volume.get('Tags', []))
    datestr = datetime.now(UTC()).strftime("%Y%m%d%H%M%S")
    if name:
        return "%s %s" % (name, datestr)
    else:
        return "%s %s" % (volume['VolumeId'], datestr)
