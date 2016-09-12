"""AWS Lambda functions for EBS Volume Snapshots"""

import boto3
import logging
from datetime import tzinfo, timedelta, datetime

DEFAULT_DAYS_TO_KEEP = 30

logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
    logger.info("Making snapshots")
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
    """Delete old snapshots older than the specified number of days

    The number of days may come from a "days" property of the CloudWatch event,
    and will default to DEFAULT_DAYS_TO_KEEP.  You can specify the "days"
    property by configuring the CloudWatch Rule, in its "inputs" section,
    by specifying a constant JSON value.  Example:
    {"account": "12345", "days": 28}

    Note that "days" should be an integer.
    """
    account = event['account']
    days_to_keep = event.get('days', DEFAULT_DAYS_TO_KEEP)
    logger.info("Deleting snapshots older than %i days" % days_to_keep)
    client = boto3.client('ec2')
    snaps = client.describe_snapshots(OwnerIds=[account])['Snapshots']
    old_snaps = (s for s in snaps if older_than(s['StartTime'], days_to_keep))
    for s in old_snaps:
        client.delete_snapshot(SnapshotId=s['SnapshotId'])
    logger.info("Done")

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
