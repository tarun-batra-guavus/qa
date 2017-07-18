************
Introduction
************

About Potluck
=============
Potluck is the automation framework written in Python for build upgrades on complete setup, running regression, sanity, functional test cases and then publish the results over intranet.
As the name potluck suggested that everyone of can contribute to the framework by writing test cases and those test cases can be picked by other teams with no or minor changes.

Why Potluck
-----------
Today most of the testing is manual or semi-manual.
Human intervention/ attention is required every now and then which makes the configuration/observation error prone. Moreover most of the servers are underutilized at non-working hours.
Almost same test cases are written by all the teams which makes the Test Cases duplicate and scattered and this further results in scattered test results.
Regression is time/resource consuming, by the time ST is able to run the regression its time to release the build

What it solves
--------------
Since Potluck is a centralized and a general framework, it can be used by all the teams working on hadoop architecture using TM platform. This results in test cases sharing which avoids duplicate effort of writing test cases. Provides a centralized location for test results, this will help us in identifying build quality criteria(good, average, bad). Multiple cycles of regression can be run day & night on the test beds.

How it solves
-------------
Framework exposes certain APIs like Connect, setMode, sendCmd, Upgrade, Reboot which can be used to do (almost) everything that a system admin/tester can do on the TM machine.

The advantage of using these APIs is that a piece of code be re-utilized and instead of executing same set of commands on number of boxes manually , just write them once and framework will execute on chosen/all machines. Test cases which are written by one team can be used by other team in same project as well as in different project. For example, Upgrade, HDFS working.

Framework also provides logging at each step of test case and exits with a pass/ fail message. The test results are placed on a central server with testBed name, date and time stamps.
