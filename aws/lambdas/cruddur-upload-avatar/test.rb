require 'aws-sdk-s3'
require 'json'
require 'jwt'

def handler(event:, context:)
    puts event
   
    s3 = Aws::S3::Resource.new
    bucket_name = ENV["UPLOADS_BUCKET_NAME"]
    object_key = "mock.jpg"

    puts({object_key: object_key}.to_json)

    obj = s3.bucket(bucket_name).object(object_key)
    url = obj.presigned_url(:put, expires_in: 60 * 5)
    url # this is the data that will be returned
    body = {url: url}.to_json
    { 
        headers: {
        "Access-Control-Allow-Headers": "*, Authorization",
        "Access-Control-Allow-Origin": ENV["ORIGIN_URL"],
        "Access-Control-Allow-Methods": "OPTIONS,GET,POST"
        },
        statusCode: 200, 
        body: body 
    }
end # def handler

ret = handler(event:{}, context:{})
puts ret