import * as aws from 'aws-sdk';
//import { inspect } from 'util';
import { cfnResponse, cfnResponseStatus } from './cfn';
import { Context, CloudFormationCustomResourceCreateEvent as CreateEvent } from 'aws-lambda';
import fetch from 'node-fetch';
import { Response } from 'node-fetch';
import { URLSearchParams } from 'url';
import * as config from './config'

aws.config.update({region: config.aws.region? config.aws.region : 'us-east-1'});

async function getRoute53(event: CreateEvent, context: Context): Promise<void> {
    //console.log('getRoute53 event:', inspect(event, false, null));
    //console.log('getRoute53 context:', inspect(context, false, null));

    if(event.RequestType !== 'Create') { // only Create is supported
        await cfnResponse(event, context, cfnResponseStatus.SUCCESS, {status: 'OK'});
        return;
    }

    if(!event.ResourceProperties.DNSZone || !event.ResourceProperties.company || !event.ResourceProperties.apiKey) {
        console.log('getRoute53: missing input parameter');
        await cfnResponse(event, context, cfnResponseStatus.FAILED, {status: 'Error', error: 'missing input parameter'});
        return;
    }
    let r53 : aws.Route53 = new aws.Route53({apiVersion: '2013-04-01'});

    let params: aws.Route53.GetHostedZoneRequest = {
        Id: event.ResourceProperties.DNSZone
    }
    let hostedZone: aws.Route53.GetHostedZoneResponse = undefined;
    try {
        hostedZone = await r53.getHostedZone(params).promise();
    }
    catch(err) {
        console.log('getRoute53: got error', err)
        await cfnResponse(event, context, cfnResponseStatus.FAILED, {status: 'Error', error: err});
        return;
    }
    console.log('read hosted zone:', JSON.stringify(hostedZone));
    let nameServers: string = undefined;
    if(hostedZone.DelegationSet.NameServers) {
        // hostedZone read
        nameServers = hostedZone.DelegationSet.NameServers.join(".\n") + '.';
        console.log('nameServers are:', nameServers);
        let res: Response = undefined;
        // this API uses x-www-form-urlencoded
        let reqBody = new URLSearchParams();
        reqBody.append('recordName', event.ResourceProperties.company);
        reqBody.append('owner', event.ResourceProperties.company);
        reqBody.append('ns', nameServers);
        reqBody.append('apikey', event.ResourceProperties.apiKey);
        console.log('Request body is: ', reqBody);

        try {
            res = await fetch(config.r53auto.url, { method: 'POST', body: reqBody});
            let text = await res.text();
            if(!text.startsWith('Success')) throw('Bad response from NS API: ' + text.substring(0, 64));
            else console.log('r53auto API returned success!');
        }
        catch(err) {
            console.log('r53auto error:', err);
            await cfnResponse(event, context, cfnResponseStatus.FAILED, {status: 'Error', error: err});
            return;
        }
        // ok
        console.log('r53auto status:', res.status);
        console.log('r53auto message:', res.statusText);
    }
    else {
        console.log('getRoute53: cannot determine nameservers')
        await cfnResponse(event, context, cfnResponseStatus.FAILED, {status: 'Error', error: 'getRoute53: cannot determine nameservers'})
    }
    let responseData = {status: 'OK', nameServers: nameServers};
    await cfnResponse(event, context, cfnResponseStatus.SUCCESS, responseData);
    return;
}

export { getRoute53 };
