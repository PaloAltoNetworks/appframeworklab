import { Context, CloudFormationCustomResourceEvent as Event } from 'aws-lambda';
import { Response  } from 'node-fetch';
import fetch from 'node-fetch';
import { UrlWithStringQuery, parse } from 'url'

enum cfnResponseStatus {
    SUCCESS = 'SUCCESS',
    FAILED = 'FAILED'
};

async function cfnResponse(event: Event, context: Context, responseStatus: cfnResponseStatus, responseData: object, physicalResourceId?: string, noEcho?: boolean): Promise<void> {

    let responseBody: string = JSON.stringify({
        Status: responseStatus,
        Reason: "See the details in CloudWatch Log Stream: " + context.logStreamName,
        PhysicalResourceId: physicalResourceId || context.logStreamName,
        StackId: event.StackId,
        RequestId: event.RequestId,
        LogicalResourceId: event.LogicalResourceId,
        NoEcho: noEcho || false,
        Data: responseData
    });

    console.log("cfnResponse body:\n", responseBody);

    let parsedUrl: UrlWithStringQuery = parse(event.ResponseURL);
    let responseUrl = 'https://' + parsedUrl.hostname + parsedUrl.path
    //console.log('cfnResponse url:', responseUrl)
    let response: Response = undefined;
    try {
        response = await fetch(responseUrl, { method: 'PUT', body: responseBody, headers: {
            "content-type": "",
            "content-length": responseBody.length.toString()
        }});
    }
    catch(err) {
        console.log('cfnResponse error:', err);
        context.done(); // TODO: is context.done correct it or shall it be called by the calling function in case of error?
        return; // TODO: propagate the exception?
    }
    console.log('cfnResponse code:', response.status);
    console.log('cfnResponse message:', response.statusText);
    context.done();
    return;
}

export { cfnResponse, cfnResponseStatus };
 
