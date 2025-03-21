resource "aws_iam_role" "lambda_role" {
  name = "spotify-lambda-role-${var.env}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}


resource "aws_iam_policy" "spotify_lambda_policy" {
  name        = "spotify-lambda-policy-${var.env}"
  description = "policy for lambda role to give access to dynamodb, logs and ecr"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
            "dynamodb:*"
        ],
        Resource = "${aws_dynamodb_table.dynamodb.arn}"
      },
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ],
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow",
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
        ],
        Resource = "*"
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "spotify_lambda_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.spotify_lambda_policy.arn
}

resource "aws_lambda_function" "lambda" {
  function_name = "spotify-lambda-${var.env}"
  package_type  = "Image"
  image_uri     = var.image_uri
  role          = aws_iam_role.lambda_role.arn
  timeout       = 120
  memory_size   = 128

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = "${aws_dynamodb_table.dynamodb.name}"
      REGION              = "${var.aws_region}"
      SPOTIFY_CLIENT_ID = "${var.client_id}"
      SPOTIFY_CLIENT_SECRET = "${var.client_secret}"
    }
  }

   vpc_config {
    subnet_ids         = ["${data.terraform_remote_state.networking.outputs.priv_sub_id}"]
    security_group_ids = ["${aws_security_group.lambda_sg.id}"]  
  }

  tags = {
    Environment = "${var.env}"
  }
}

resource "aws_security_group" "lambda_sg" {
  name        = "lambda-sg-${var.env}"
  description = "spotify lambda function"
  vpc_id      = data.terraform_remote_state.networking.outputs.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Environment = var.env
  }
}

resource "aws_iam_policy" "lambda_vpc_policy" {
  name        = "spotify-lambda-vpc-policy-${var.env}"
  description = "Allow Lambda to interact with VPC resources"
  policy      = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeSubnets",
          "ec2:DescribeVpcs",
          "ec2:CreateNetworkInterface",
          "ec2:DeleteNetworkInterface",
          "ec2:DescribeNetworkInterfaces"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}


resource "aws_iam_role_policy_attachment" "lambda_vpc_policy_attachment" {
  policy_arn = aws_iam_policy.lambda_vpc_policy.arn
  role       = aws_iam_role.lambda_role.name
}

resource "aws_lambda_permission" "api_gateway_invoke" {
  statement_id  = "AllowAPIGatewayInvoke-${var.env}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.spotify.execution_arn}/*/*"
}