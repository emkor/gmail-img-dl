# gmail-img-dl
CLI tool for retrieving image attachments from GMail messages (specifically from Reolink security cameras)

## prerequisites
- Unix, `make`, `git`, `python3` with `pip`

## installation
- `git clone https://github.com/emkor/gmail-img-dl.git && cd gmail-img-dl`
- `make venv test build`
- system-wide installation: `sudo pip install dist/gmail-img-dl-*.tar.gz`

## usage
- set env variables before use:
    - `GMAIL_USER` (basically, gmail address, like `user@gmail.com`)
    - `GMAIL_PASSWORD`, self-explanatory
- simple example: `gmail_dl ./emails` will download all attachments from emails sent yesterday in the `./emails` directory, without removing the emails from GMail
- advanced example: `gmail_dl ~/emails --since 2019-04-01 --till 2019-05-01 --log ~/gmail_dl.log --rm`
    - this call will download attachments from emails sent in April 2019
    - store them under `~/emails`
    - log all actions into `~/gmail_dl.log`
    - trash all emails with downloaded attachments