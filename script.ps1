# Define the target times in GMT
$timeGMT1 = "16:00z" # 4pm UTC is 12pm ET
$timeGMT2 = "20:00z" #8PM UTC is 4pm ET 

$localTime1 = Get-Date $timeGMT1 -format "hh:mm"
$localTime2 = Get-Date $timeGMT2 -format "hh:mm"

#getting other variables
$pythonPath = Get-Command python 
if(! $pythonPath){
    Write-Error "Python not detected"
    exit 1 
}

#checking library, this could also be done with a venv
$requests_installed = $(pip show requests)
if(! $requests_installed){
    Write-Error "Requests library not installed. Please run: pip install requests"
    exit 1
}

$script = "check_website_script.py"

$action = New-ScheduledTaskAction -Execute $pythonPath -Argument $(Join-Path $(Get-Location) $script)
$trigger1 = New-ScheduledTaskTrigger -Once -At $timeGMT1
$trigger2 = New-ScheduledTaskTrigger -Once -At $timeGMT2

Register-ScheduledTask -TaskName "OneTimeTask12PM_ET" -Trigger $trigger1 -Action $action -Description "One-time task at 12:00 PM ET adjusted for local time"
Register-ScheduledTask -TaskName "OneTimeTask4PM_ET" -Trigger $trigger1 -Action $action -Description "One-time task at 4:00 PM ET adjusted for local time"
