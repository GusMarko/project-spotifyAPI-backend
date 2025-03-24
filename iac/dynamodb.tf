resource "aws_dynamodb_table" "dynamodb" {
  name = "spotify-data-${var.env}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "artistName"
  range_key = "dataType"

  attribute {
    name = "artistName"
    type = "S"
  }

  attribute {
    name = "dataType"
    type = "S"
  }

    tags = {
    Environment = "${var.env}"
  }
}
