import * as aws from 'aws-sdk';
//import { inspect } from 'util';
import { cfnResponse, cfnResponseStatus } from './cfn';
import { Context, CloudFormationCustomResourceEvent as Event, CloudFormationCustomResourceCreateEvent as CreateEvent, CloudFormationCustomResourceDeleteEvent as DeleteEvent } from 'aws-lambda';
import * as config from './config'

const region = process.env['AWS_REGION'] || config.aws.defaultRegion || 'us-east-1';
aws.config.update({region: region});

async function listS3Buckets(event: CreateEvent, context: Context): Promise<void> {
    //console.log('listS3Buckets event:', inspect(event, false, null));
    //console.log('listS3bucketsBucket context:', inspect(context, false, null));
    let s3Client: aws.S3 = new aws.S3();
    let buckets: aws.S3.ListBucketsOutput = undefined;
    try {
        buckets = await s3Client.listBuckets().promise();
    }
    catch(err) {
        console.log('listS3Buckets: got error', err);
        await cfnResponse(event, context, cfnResponseStatus.FAILED, {status: 'Error', error: err});
        return;
    }
    console.log('S3buckets: ', buckets.Buckets);
    await cfnResponse(event, context, cfnResponseStatus.SUCCESS, { status: 'OK', buckets: JSON.stringify(buckets.Buckets)});
    return;
}

async function emptyS3Bucket(event: DeleteEvent, context: Context): Promise<void> {
    //console.log('emptyS3Bucket event:', inspect(event, false, null));
    //console.log('emptyS3Bucket context:', inspect(context, false, null));

    if(!event.ResourceProperties.targetBucket) {
        console.log('emptyS3Bucket: missing input parameter');
        await cfnResponse(event, context, cfnResponseStatus.FAILED, {status: 'Error', error: 'missing input parameter'});
        return;
    }

    try {
        let s3Client: aws.S3 = new aws.S3();
        let s3Objects = await s3Client.listObjects({ Bucket: event.ResourceProperties.targetBucket}).promise();
        if(s3Objects.Contents.length) {
            for (const o of s3Objects.Contents) {
                if(!o.Key) continue;
                let params: aws.S3.DeleteObjectRequest = {
                    Bucket: event.ResourceProperties.targetBucket,
                    Key: o.Key
                }
                await s3Client.deleteObject(params).promise();
                console.log('deleted object:', event.ResourceProperties.targetBucket + '/' + o.Key)
            };
        }
        else {
            console.log('emptyS3Bucket: no contents found');
        };
    }
    catch(err) {
        console.log('emptyS3Bucket: got error', err);
        await cfnResponse(event, context, cfnResponseStatus.FAILED, {status: 'Error', error: err});
        return;
    };
    
    console.log('emptyS3Bucket: delete completed!');
    await cfnResponse(event, context, cfnResponseStatus.SUCCESS, {status:'OK'});
    return;
}

async function copyS3Bucket(event: CreateEvent, context: Context): Promise<void> {
    //console.log('copyS3Bucket event:', inspect(event, false, null));
    //console.log('copyS3Bucket context:', inspect(context, false, null));

    if(!event.ResourceProperties.sourceBucket || !event.ResourceProperties.targetBucket) {
        console.log('copyS3Bucket: missing input parameter');
        await cfnResponse(event, context, cfnResponseStatus.FAILED, {status: 'Error', error: 'missing input parameter'});
        return;
    }
    if(event.ResourceProperties.sourceBucket === event.ResourceProperties.targetBucket) {
        console.log('copyS3Bucket: source and destination bucket cannot be the same');
        await cfnResponse(event, context, cfnResponseStatus.FAILED, {status: 'Error', error: 'source and destination bucket cannot be the same'});
        return;
    }

    try {
        let s3Client: aws.S3 = new aws.S3();
        let s3Objects = await s3Client.listObjects({ Bucket: event.ResourceProperties.sourceBucket}).promise();
        if(s3Objects.Contents.length) {
            for (const o of s3Objects.Contents) {
                if(!o.Key) continue;
                let params: aws.S3.CopyObjectRequest = {
                    Bucket: event.ResourceProperties.targetBucket,
                    CopySource: event.ResourceProperties.sourceBucket + '/' + o.Key,
                    Key: o.Key
                }
                await s3Client.copyObject(params).promise();
                console.log('copied object:', event.ResourceProperties.sourceBucket + '/' + o.Key, 'to:', event.ResourceProperties.targetBucket + '/' + o.Key)
            };
        }
        else {
            console.log('copyS3Bucket: no contents found');
            await cfnResponse(event, context, cfnResponseStatus.FAILED, {status:'Error', error: 'no contents found'});
            return;
        };
    }
    catch(err) {
        console.log('copyS3Bucket: got error', err);
        await cfnResponse(event, context, cfnResponseStatus.FAILED, {status: 'Error', error: err});
        return;
    };
    
    console.log('copyS3Bucket: copy completed!');
    await cfnResponse(event, context, cfnResponseStatus.SUCCESS, {status:'OK'});
    return;
}

async function writeAuthCode(event: CreateEvent, context: Context): Promise<void> {
    //console.log('writeAuthCode event:', inspect(event, false, null));
    //console.log('writeAuthCode context:', inspect(context, false, null));

    if(event.RequestType !== 'Create') { // only Create is supported
        await cfnResponse(event, context, cfnResponseStatus.SUCCESS, {status: 'OK'});
        return;
    }

    if(!event.ResourceProperties.authCode || !event.ResourceProperties.targetBucket || !event.ResourceProperties.keyName) {
        console.log('writeAuthCode: missing input parameter');
        await cfnResponse(event, context, cfnResponseStatus.FAILED, {status: 'Error', error: 'missing input parameter'});
        return;
    }

    try {
        let s3Client: aws.S3 = new aws.S3();
        let s3params: aws.S3.PutObjectRequest = {
            Bucket: event.ResourceProperties.targetBucket,
            Key: event.ResourceProperties.keyName,
            Body: event.ResourceProperties.authCode
        };
        let out: aws.S3.PutObjectOutput = await s3Client.putObject(s3params).promise();
        console.log('writeAuthCode putObject output is:', JSON.stringify(out));
    }

    catch(err) {
        console.log('writeAuthCode: got error', err);
        await cfnResponse(event, context, cfnResponseStatus.FAILED, {status: 'Error', error: err});
        return;
    };
    
    console.log('writeAuthCode: authcode written!');
    await cfnResponse(event, context, cfnResponseStatus.SUCCESS, {status:'OK'});
    return;
}

async function handleS3Bucket(event: Event, context: Context): Promise<void> {
    //console.log('handleS3Bucket event:', inspect(event, false, null));
    //console.log('handleS3Bucket context:', inspect(context, false, null));    

    switch(event.RequestType) {
        case 'Create': {
            await copyS3Bucket(event, context);
            return; // no cfnResponse here as it's handle by inner function
        }
        case 'Delete': {
            await emptyS3Bucket(event, context);
            return; // no cfnResponse here as it's handle by inner function
        }

        default: {
            console.log('handleS3Bucket: RequestType not handled');
            await cfnResponse(event, context, cfnResponseStatus.FAILED, {status: 'Error', error: 'RequestType not handled'});
            return;            
        }
    }
}

export { listS3Buckets, handleS3Bucket, writeAuthCode };
