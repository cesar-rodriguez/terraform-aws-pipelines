resource "aws_kms_key" "pipeline_key" {
  description             = "KMS key for ${var.project_name} terraform pr pipeline"
  deletion_window_in_days = 30
  policy                  = "${data.aws_iam_policy_document.pipeline_key.json}"
  enable_key_rotation     = true
}

resource "aws_kms_alias" "pipeline_key" {
  name          = "alias/${var.project_name}-terraform-pr"
  target_key_id = "${aws_kms_key.pipeline_key.key_id}"
}

data "aws_iam_policy_document" "pipeline_key" {
  statement {
    sid = "Key Administrators"

    actions = [
      "kms:Create*",
      "kms:Describe*",
      "kms:Enable*",
      "kms:List*",
      "kms:Put*",
      "kms:Update*",
      "kms:Revoke*",
      "kms:Disable*",
      "kms:Get*",
      "kms:Delete*",
      "kms:TagResource",
      "kms:UntagResource",
      "kms:ScheduleKeyDeletion",
      "kms:CancelKeyDeletion",
    ]

    resources = ["*"]

    principals {
      type = "AWS"

      identifiers = [
        "${data.aws_caller_identity.current.user_id}",
      ]
    }
  }

  statement {
    sid = "Allows usage of key"

    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:DescribeKey",
      "kms:List*",
      "kms:Get*",
    ]

    resources = ["*"]

    principals {
      type = "AWS"

      identifiers = [
        "${data.aws_caller_identity.current.user_id}",
        "${aws_iam_role.codebuild.arn}",
        "${aws_iam_role.codepipeline.arn}",
        "${aws_iam_role.poller_create.arn}",
        "${aws_iam_role.poller_delete.arn}",
        "${aws_iam_role.pipeline_create.arn}",
      ]
    }
  }

  statement {
    sid = "Allows attachment of persistent resources"

    actions = [
      "kms:CreateGrant",
      "kms:ListGrants",
      "kms:RevokeGrant",
    ]

    resources = ["*"]

    principals {
      type = "AWS"

      identifiers = [
        "${data.aws_caller_identity.current.user_id}",
      ]
    }
  }
}
