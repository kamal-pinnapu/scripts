#!/bin/bash
set -e
repos=$(bb list -u $BB_USERNAME -p $BB_PASSWORD --private | grep $BB_ORG | cut -d' ' -f3 | cut -d'/' -f2)
for repo in $repos; do
  echo
  echo "* Processing $repo..."
  echo
  git clone --bare git@bitbucket.org:$BB_ORG/$repo.git 
  cd $repo.git
  echo
  echo "* $repo cloned, now creating on github..."  
  echo
  curl -u $GH_USERNAME:$GH_PASSWORD https://api.github.com/orgs/$GH_ORG/repos -d "{\"name\": \"$repo\", \"private\": true}"
  echo
  echo "* mirroring $repo to github..."  
  echo
  git push --mirror git@github.com:$GH_ORG/$repo.git && \
    bb delete -u $BB_USERNAME -p $BB_PASSWORD --owner $BB_ORG $repo    
  cd ..  
done
