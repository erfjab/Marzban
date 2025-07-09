# Project Description  

This version of Marzban (similar to Marzneshin) has been customized for the MoreBot sales bot.  

## Setup Instructions  

After installing the original version of Marzban and making any desired changes, to use this version, replace your Marzban tag in the configuration:  

From:  
```  
services:  
  marzban:  
    image: gozargah/marzban:latest  
```  

To:  
```  
services:  
  marzban:  
    image: ghcr.io/erfjab/marzban:master  
```  

Then, add these two values to your `.env` file:  

```  
MOREBOT_SECRET=""  # Secret key received from MoreBot (Server Info section)  
MOREBOT_LICENSE="" # License key provided by the admin (@ErfJab)  
```  

Finally, update and restart Marzban. Done.
