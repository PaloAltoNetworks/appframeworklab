import * as lambda from '../src'
import { Context, CloudFormationCustomResourceCreateEvent as CreateEvent, CloudFormationCustomResourceDeleteEvent as DeleteEvent } from 'aws-lambda';

import * as dotenv from "dotenv";

dotenv.config();
const apiKey = process.env.R53AUTOAPIKEY ? process.env.R53AUTOAPIKEY : undefined

if(!apiKey) {
    console.log('R53AUTOAPIKEY not defined in env!');
    process.exit(-1);
}

async function test(): Promise<void> {
    try {
        let getRoute53ev: CreateEvent = {
            RequestType: 'Create',
            ServiceToken: 'ggggglambda',
            ResourceProperties: {
                ServiceToken: 'gggglambda',
                DNSZone: 'Z2UUVZVTWDCZZ1',
                company: 'test111',
                apiKey: apiKey
            },
            ResponseURL: 'http://localhost:12831',
            StackId: 'abcde',
            RequestId: '12345',
            LogicalResourceId: 'fffff',
            ResourceType: 'lambda'
        };


        let copyS3Bucketev: CreateEvent = {
            RequestType: 'Create',
            ServiceToken: 'ggggglambda',
            ResourceProperties: {
                ServiceToken: 'gggglambda',
                sourceBucket: 'appf-bootstrap-conf',
                targetBucket: 'appf-test3'
            },
            ResponseURL: 'http://localhost:12831',
            StackId: 'abcde',
            RequestId: '12345',
            LogicalResourceId: 'fffff',
            ResourceType: 'lambda'
        };

        let emptyS3Bucketev: DeleteEvent = {
            RequestType: 'Delete',
            ServiceToken: 'ggggglambda',
            ResourceProperties: {
                ServiceToken: 'gggglambda',
                targetBucket: 'appf-test3'
            },
            ResponseURL: 'http://localhost:12831',
            StackId: 'abcde',
            RequestId: '12345',
            LogicalResourceId: 'fffff',
            ResourceType: 'lambda',
            PhysicalResourceId: 'physid123'
        };

        let listS3Bucketsev: CreateEvent = {
            RequestType: 'Create',
            ServiceToken: 'ggggglambda',
            ResourceProperties: {
                ServiceToken: 'gggglambda',
            },
            ResponseURL: 'https://localhost:18231',
            StackId: 'abcde',
            RequestId: '12345',
            LogicalResourceId: 'fffff',
            ResourceType: 'lambda'
        };

        let writeAuthCodeev: CreateEvent = {
            RequestType: 'Create',
            ServiceToken: 'ggggglambda',
            ResourceProperties: {
                ServiceToken: 'gggglambda',
                keyName: 'license/authcodes',
                targetBucket: 'appframework-test2',
                authCode: 'I123456'
            },
            ResponseURL: 'http://localhost:12831',
            StackId: 'abcde',
            RequestId: '12345',
            LogicalResourceId: 'fffff',
            ResourceType: 'lambda'
        };

        let createKeyPairev: CreateEvent = {
            RequestType: 'Create',
            ServiceToken: 'ggggglambda',
            ResourceProperties: {
                ServiceToken: 'gggglambda',
                keyName: 'ngfwkeytest',
                targetBucket: 'appframework-test2',
                keyPath: 'keys'
            },
            ResponseURL: 'http://localhost:12831',
            StackId: 'abcde',
            RequestId: '12345',
            LogicalResourceId: 'fffff',
            ResourceType: 'lambda'
        };

        let deleteKeyPairev: DeleteEvent = {
            RequestType: 'Delete',
            ServiceToken: 'ggggglambda',
            ResourceProperties: {
                ServiceToken: 'gggglambda',
                keyName: 'ngfwkeytest',
            },
            ResponseURL: 'http://localhost:12831',
            StackId: 'abcde',
            RequestId: '12345',
            LogicalResourceId: 'fffff',
            ResourceType: 'lambda',
            PhysicalResourceId: 'entro_reggio'
        };

        let ctx : Context = {
            callbackWaitsForEmptyEventLoop: true,
            functionName: 'testFunction',
            functionVersion: '666',
            invokedFunctionArn: 'aws:arn:666::666:666',
            memoryLimitInMB: 128,
            awsRequestId: 'req666',
            logGroupName: 'loggroup1',
            logStreamName: 'logstream1',
            getRemainingTimeInMillis: () => 666,
            done: () => console.log('done'),
            fail: () => console.log('fail'),
            succeed: (a: any): void => console.log('succeed'),
        }

        // await lambda.handleKeyPair(createKeyPairev, ctx);
        // await lambda.handleKeyPair(deleteKeyPairev, ctx);
        //await lambda.handleS3Bucket(copyS3Bucketev, ctx);
        await lambda.handleS3Bucket(emptyS3Bucketev, ctx);
        // await lambda.listS3Buckets(listS3Bucketsev, ctx);
        // await lambda.getRoute53(getRoute53ev, ctx);
        // await lambda.writeAuthCode(writeAuthCodeev, ctx);

    }
    catch(err) {
        console.log('error:', err);
    };
}

test();
