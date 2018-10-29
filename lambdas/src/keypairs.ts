import * as aws from 'aws-sdk';
//import { inspect } from 'util';
import { cfnResponse, cfnResponseStatus } from './cfn';
import { Context, CloudFormationCustomResourceEvent as Event, CloudFormationCustomResourceCreateEvent as CreateEvent, CloudFormationCustomResourceDeleteEvent as DeleteEvent } from 'aws-lambda';
import * as config from './config'

aws.config.update({region: config.aws.region? config.aws.region : 'us-east-1'});

async function createKeyPair(event: CreateEvent, context: Context): Promise<void> {
    //console.log('createKeyPair event:', inspect(event, false, null));
    //console.log('createKeyPair context:', inspect(context, false, null));    

    if(!event.ResourceProperties.keyName || !event.ResourceProperties.targetBucket || !event.ResourceProperties.keyPath || !event.ResourceProperties.stackName) {
        console.log('createKeyPair: missing input parameter');
        await cfnResponse(event, context, cfnResponseStatus.FAILED, {status: 'Error', error: 'missing input parameter'});
        return;
    };

    let ec2 : aws.EC2 = new aws.EC2({apiVersion: '2016-11-15'});

    let keyPairName: string = event.ResourceProperties.keyName + '-' + event.ResourceProperties.stackName;
    console.log('createKeyPair: keyPairName is', keyPairName);

    let params: aws.EC2.CreateKeyPairRequest = {
        KeyName: keyPairName
    };

    let keypair: aws.EC2.KeyPair = undefined;
    try {
        keypair = await ec2.createKeyPair(params).promise();
    }
    catch(err) {
        console.log('createKeyPair: got error', err);
        await cfnResponse(event, context, cfnResponseStatus.FAILED, {status: 'Error', error:err});
        return;
    };
    console.log('createKeyPair created keypair:', keypair.KeyName);
 
    if(keypair.KeyMaterial) {
        let fullKeyPath: string = event.ResourceProperties.keyPath + '/' + event.ResourceProperties.keyName + '.pem';
        console.log('createKeyPair targetBucket:', event.ResourceProperties.targetBucket);
        console.log('createKeyPair fullKeyPath:', fullKeyPath);

        // keypair created
        let s3Client: aws.S3 = new aws.S3();
        try {
            let s3params: aws.S3.PutObjectRequest = {
                Bucket: event.ResourceProperties.targetBucket,
                Key: fullKeyPath,
                Body: keypair.KeyMaterial
            };
            let out: aws.S3.PutObjectOutput = await s3Client.putObject(s3params).promise();
            console.log('createKeyPair putObject output is:', JSON.stringify(out));
        }
        catch(err) {
            console.log('createKeyPair: got error', err);
            await cfnResponse(event, context, cfnResponseStatus.FAILED, {status: 'Error', error:err});
            return;
        }
    }
    await cfnResponse(event, context, cfnResponseStatus.SUCCESS, {status:'OK'});
    return;
}

async function deleteKeyPair(event: DeleteEvent, context: Context): Promise<void> {
    //console.log('deleteKeyPair event:', inspect(event, false, null));
    //console.log('deleteKeyPair context:', inspect(context, false, null));    

    if(!event.ResourceProperties.keyName) {
        console.log('deleteKeyPair: missing input parameter');
        await cfnResponse(event, context, cfnResponseStatus.FAILED, {status: 'Error', error: 'missing input parameter'});
        return;
    };

    let ec2 : aws.EC2 = new aws.EC2({apiVersion: '2016-11-15'});
    let keyPairName: string = event.ResourceProperties.keyName + '-' + event.ResourceProperties.stackName;
    console.log('createKeyPair: keyPairName is', keyPairName);

    let params: aws.EC2.DeleteKeyPairRequest = {
        KeyName: keyPairName
    };

    let keypair: aws.EC2.KeyPair = undefined;
    try {
        await ec2.deleteKeyPair(params).promise();
    }
    catch(err) {
        console.log('deleteKeyPair: got error', err);
        await cfnResponse(event, context, cfnResponseStatus.FAILED, {status: 'Error', error:err});
        return;
    };
    
    console.log('deleteKeyPair deleted keypair');
    await cfnResponse(event, context, cfnResponseStatus.SUCCESS, {status:'OK'});
    return;
}

async function handleKeyPair(event: Event, context: Context): Promise<void> {
    //console.log('handleKeyPair event:', inspect(event, false, null));
    //console.log('handleKeyPair context:', inspect(context, false, null));    

    switch(event.RequestType) {
        case 'Create': {
            await createKeyPair(event, context);
            return; // no cfnResponse here as it's handle by inner function
        }
        case 'Delete': {
            await deleteKeyPair(event, context);
            return; // no cfnResponse here as it's handle by inner function
        }

        default: {
            console.log('handleKeyPair: RequestType not handled');
            await cfnResponse(event, context, cfnResponseStatus.FAILED, {status: 'Error', error: 'RequestType not handled'});
            return;            
        }
    }
}

export { handleKeyPair };
