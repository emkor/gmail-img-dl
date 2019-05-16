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
- simple: `gmail_dl` will download all attachments from emails sent yesterday in the place where it was called, without removing the emails from GMail
- advanced: `gmail_dl --since 2019-04-01 --till 2019-05-01 --dir ~/emails --log ~/gmail_dl.log --rm`
    - this call will download attachments from emails sent in April 2019
    - store them in `~/emails`
    - log all actions into `~/gmail_dl.log`
    - trash all emails with downloaded attachments